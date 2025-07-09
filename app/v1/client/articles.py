import os
import asyncio
import aiohttp
from doi2pdf import doi2pdf
from dotenv import load_dotenv
from app.v1.utils.constants import USER_AGENT_TEMPLATE
from app.v1.schemas.articles import (
    CrossRefParams,
    ArticleResponse,
    ArticleInput,
)
from app.v1.repositories.articles import ArticleRepository
from app.v1.utils.utils import create_ssl_context
import tempfile
from app.v1.utils.storage import AzureBlobStorageClient
from app.v1.utils.utils import create_file_name
import logging
from typing import List
from app.v1.utils.exception_handling import handle_exception

logger = logging.getLogger(__name__)


class ExtractResearchArticles:
    def __init__(self):
        load_dotenv()

        self._configure_from_env()
        self.azure_client = AzureBlobStorageClient()
        self.logger = logging.getLogger(__name__)
        self.article_cls = ArticleRepository()

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

    @handle_exception(
        logger,
        input_identifier_key="query",
        operation_desc="fetching DOIs with query:",
        include_error_type=True,
    )
    async def get_dois_from_crossref(self, query, max_articles):
        crossref_connector = create_ssl_context()

        params = CrossRefParams(query=query, rows=max_articles).model_dump()
        headers = self._get_crossref_headers()

        async with aiohttp.ClientSession(connector=crossref_connector) as session:
            async with session.get(
                self.crossref_base_url, params=params, headers=headers
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return self.extract_article_info(data)

    @handle_exception(
        logger, operation_desc="checking for open access", include_error_type=True
    )
    async def check_for_open_access(self, article_list):
        open_article_list = []
        open_access_connector = create_ssl_context()

        async with aiohttp.ClientSession(connector=open_access_connector) as session:
            for article in article_list:
                unpaywell_url = self._get_unpaywall_url(article["doi"])

                is_open_access = await self.check_article_access(session, unpaywell_url)
                if is_open_access:
                    open_article_list.append(article)

            if not open_article_list:
                self.logger.error("No open-access articles found.")
                raise Exception("No open-access articles found.")

        return open_article_list

    @handle_exception(
        logger, operation_desc="checking for open access", include_error_type=True
    )
    async def check_article_access(self, session, url):
        async with session.get(url) as response:
            data = await response.json()
            return data.get("is_oa")

    @handle_exception(
        logger, operation_desc="extracting articles", include_error_type=True
    )
    def extract_article_info(self, data):
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
        return article_list

    @handle_exception(
        logger, operation_desc="downloading papers", include_error_type=True
    )
    async def download_papers(self, open_article_list) -> List[ArticleResponse]:
        for article in open_article_list:
            article["file_name"] = create_file_name(article["title"][0])

        tasks = [
            self.download_and_upload_paper(article) for article in open_article_list
        ]

        # Process all downloads in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        exported_articles = [article for article in results if article is not None]

        if exported_articles:
            pass
        else:
            raise ValueError("No articles downloaded.")

        return exported_articles

    @handle_exception(
        logger,
        operation_desc="uploading to Azure Blob Storage",
        include_error_type=True,
    )
    async def upload_to_azure(self, article, pdf_content):
        # Upload directly from memory
        blob_url = await asyncio.to_thread(
            self.azure_client.upload_pdf_from_memory,
            pdf_content,
            article["file_name"],
        )
        article["blob_url"] = blob_url

        return article

    @handle_exception(
        logger,
        output_identifier_key="doi",
        operation_desc="downloading and uploading paper with doi:",
        include_error_type=True,
    )
    async def download_and_upload_paper(self, article):
        pdf_content = await self.get_pdf_content(article["doi"])

        if not pdf_content:
            self.logger.warning(
                f"Warning: No PDF content found for DOI: {article['doi']}"
            )
            return None

        # Upload directly from memory
        article = await self.upload_to_azure(article, pdf_content)

        return article

    @handle_exception(
        logger,
        input_identifier_key="doi",
        operation_desc="downloading PDF for DOI:",
        include_error_type=True,
    )
    async def get_pdf_content(self, doi):
        """Get the PDF content in memory by first writing to a temporary file"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_path = temp_file.name

        try:
            # Download to the temporary file
            await asyncio.to_thread(doi2pdf, doi, output=temp_path)
        except Exception as e:
            self.logger.warning(f"Warning: Downloading PDF for DOI {doi}: {e}")
            return None

        # Check if file exists and has content
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            self.logger.warning(
                f"Warning: Downloaded PDF for DOI {doi} is empty or missing"
            )
            return None

        # Read the file content into memory
        with open(temp_path, "rb") as f:
            content = f.read()

        try:
            os.unlink(temp_path)
        except Exception as e:
            self.logger.warning(
                f"Warning: Failed to remove temporary file {temp_path}: {e}"
            )

        return content

    @handle_exception(
        logger,
        operation_desc="searching and downloading open papers.",
        include_error_type=True,
    )
    async def search_and_download_open_papers(self, article_input: ArticleInput):
        article_list = await self.get_dois_from_crossref(**article_input.model_dump())

        open_article_list = await self.check_for_open_access(article_list)

        downloaded_articles = await self.download_papers(open_article_list)

        articles_uploaded_db = await self.article_cls.save_downloaded_articles(
            downloaded_articles
        )

        return articles_uploaded_db
