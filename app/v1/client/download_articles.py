import os
import asyncio
import aiohttp
from doi2pdf import doi2pdf
import string
from dotenv import load_dotenv
import requests
from app.v1.utils.constants import USER_AGENT_TEMPLATE
from app.v1.schemas.download_articles import CrossRefParams, Article
from app.v1.utils.utils import create_ssl_context


class ExtractResearchArticles:
    def __init__(self, max_articles=10):
        self.max_articles = max_articles

        load_dotenv()

        # Validate required environment variables
        required_vars = ["CROSSREF_BASE_URL", "EMAIL", "JOURNAL_ARTICLE_DIRECTORY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise Exception(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        self._configure_from_env()

    def _configure_from_env(self):
        required_vars = [
            "CROSSREF_BASE_URL",
            "EMAIL",
            "JOURNAL_ARTICLE_DIRECTORY",
            "UNPAYWALL_BASE_URL",
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise Exception(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        self.email = os.getenv("EMAIL")
        self.crossref_base_url = os.getenv("CROSSREF_BASE_URL")
        self.unpaywall_base_url = os.getenv("UNPAYWALL_BASE_URL")
        self.output_directory = os.getenv("JOURNAL_ARTICLE_DIRECTORY")

        self.user_agent = USER_AGENT_TEMPLATE.format(email=self.email)

    def _get_crossref_headers(self):
        """Return headers for Crossref API requests"""
        return {"User-Agent": self.user_agent}

    def _get_unpaywall_url(self, doi):
        """Generate the appropriate Unpaywall URL for a given DOI"""
        return f"{self.unpaywall_base_url}/{doi}?email={self.email}"

    async def get_dois_from_crossref(self, query):
        params = CrossRefParams(query=query).model_dump()
        headers = self._get_crossref_headers()

        connector = create_ssl_context()

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    self.crossref_base_url, params=params, headers=headers
                ) as response:
                    # response = requests.get(self.crossref_base_url, params=params, headers=headers)
                    if response.status == 200:
                        data = await response.json()

                        article_list = []
                        for item in data["message"]["items"]:
                            article = Article(
                                DOI=item["DOI"],
                                title=item["title"],
                                author=item["author"],
                                year_published=item["published"]["date-parts"][0][0],
                                URL=item["URL"],
                                abstract=item.get("abstract"),
                            )
                            article_list.append(article.model_dump())
                    else:
                        raise Exception(f"Error fetching DOIs: {response.status}")

            return article_list

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error fetching DOIs: {e}")

    async def check_for_open_access(self, article_list):
        open_article_list = []

        connector = create_ssl_context()

        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []

            for article in article_list:
                doi = article["doi"]
                unpaywell_url = self._get_unpaywall_url(doi)
                # response = requests.get(unpaywell_url)
                tasks.append(
                    self._check_article_access(session, unpaywell_url, article)
                )

            results = await asyncio.gather(*tasks, return_exceptions=False)

            for result in results:
                if result and not isinstance(result, Exception):
                    open_article_list.append(result)

        if len(open_article_list) == 0:
            raise Exception("No open-access articles found.")

        return open_article_list

    async def _check_article_access(self, session, url, article):
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("is_oa"):
                    return article
            return None

    @staticmethod
    def create_file_name(title):
        remove_punctuation = str.maketrans("", "", string.punctuation)

        return (
            title.translate(remove_punctuation).lower().replace(" ", "_").lower()[0:40]
            + ".pdf"
        )

    async def download_papers(self, open_article_list):
        os.makedirs(os.path.dirname(self.output_directory), exist_ok=True)

        exported_articles = []
        download_tasks = []

        for article in open_article_list:
            file_name = self.create_file_name(article["title"][0])
            article["file_name"] = file_name

            output_path = os.path.join(self.output_directory, file_name)
            download_tasks.append(
                self._download_single_paper(article["doi"], output_path, article)
            )

        results = await asyncio.gather(*download_tasks, return_exceptions=False)

        for article in results:
            if article:
                exported_articles.append(article)

            doi2pdf(article["doi"], output=output_path)

        if len(exported_articles) == 0:
            raise Exception("No articles downloaded.")

        return exported_articles

    async def _download_single_paper(self, doi, output_path, article):
        await asyncio.to_thread(doi2pdf, doi, output=output_path)

        if os.path.exists(output_path):
            return article
        else:
            return None

    async def search_and_download_open_papers(self, query):
        article_list = await self.get_dois_from_crossref(query)

        open_article_list = await self.check_for_open_access(article_list)

        downloaded_articles = await self.download_papers(open_article_list)

        return downloaded_articles


if __name__ == "__main__":

    async def main():
        query = "multi-agent workflows"
        extract_cls = ExtractResearchArticles()
        results = await extract_cls.search_and_download_open_papers(query)

        print([result["title"] for result in results])

    asyncio.run(main())
