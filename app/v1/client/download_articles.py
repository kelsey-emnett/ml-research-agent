import os
import asyncio
import aiohttp
from doi2pdf import doi2pdf
import string
from dotenv import load_dotenv
import requests
from app.v1.utils.constants import USER_AGENT_TEMPLATE
from app.v1.schemas.download_articles import (
    CrossRefParams,
    ArticleResponse,
    ArticleInput,
)
from app.v1.utils.utils import create_ssl_context
import tempfile
from app.v1.utils.storage import AzureBlobStorageClient


class ExtractResearchArticles:
    def __init__(self):
        load_dotenv()

        self._configure_from_env()
        self.azure_client = AzureBlobStorageClient()

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

        self.connector = create_ssl_context()

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

    async def get_dois_from_crossref(self, query, max_articles):
        params = CrossRefParams(query=query, rows=max_articles).model_dump()
        headers = self._get_crossref_headers()

        try:
            async with aiohttp.ClientSession(connector=self.connector) as session:
                async with session.get(
                    self.crossref_base_url, params=params, headers=headers
                ) as response:
                    # response = requests.get(self.crossref_base_url, params=params, headers=headers)
                    if response.status == 200:
                        data = await response.json()

                        article_list = []
                        for item in data["message"]["items"]:
                            article = ArticleResponse(
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

        async with aiohttp.ClientSession(connector=self.connector) as session:
            tasks = []

            for article in article_list:
                doi = article["doi"]
                unpaywell_url = self._get_unpaywall_url(doi)

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
        exported_articles = []
        download_tasks = []

        async with aiohttp.ClientSession(connector=self.connector) as session:
            for article in open_article_list:
                file_name = self.create_file_name(article["title"][0])
                article["file_name"] = file_name

                download_tasks.append(
                    self.download_and_upload_paper(
                        article["doi"], file_name, article, session
                    )
                )

            results = await asyncio.gather(*download_tasks, return_exceptions=False)

        for article in results:
            if article:
                exported_articles.append(article)

        if len(exported_articles) == 0:
            raise Exception("No articles downloaded.")

        return exported_articles

    # async def download_single_paper(self, doi, output_path, article):
    #     await asyncio.to_thread(doi2pdf, doi, output=output_path)
    #
    #     if os.path.exists(output_path):
    #         return article
    #     else:
    #         return None

    async def download_and_upload_paper(self, doi, file_name, article, session):
        try:
            pdf_content = await self.get_pdf_content(doi)
            if pdf_content:
                # Upload directly from memory
                blob_url = self.azure_client.upload_pdf_from_memory(
                    pdf_content, file_name
                )
                article["blob_url"] = blob_url
                return article

        except Exception:
            return None

    async def get_pdf_content(self, doi):
        """Get the PDF content in memory by first writing to a temporary file"""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_path = temp_file.name

            # Download to the temporary file
            await asyncio.to_thread(doi2pdf, doi, output=temp_path)

            # Read the file content into memory
            with open(temp_path, "rb") as f:
                content = f.read()

            # Delete the temporary file
            os.unlink(temp_path)

            return content
        except Exception as e:
            print(f"Error downloading PDF for DOI {doi}: {str(e)}")
            return None

    async def search_and_download_open_papers(self, article_input: ArticleInput):
        article_list = await self.get_dois_from_crossref(**article_input.model_dump())

        open_article_list = await self.check_for_open_access(article_list)

        downloaded_articles = await self.download_papers(open_article_list)

        return downloaded_articles
