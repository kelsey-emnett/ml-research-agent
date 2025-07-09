from app.v1.repositories.base import BaseRepository
from app.v1.schemas.articles import ArticleResponse
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime
from app.v1.utils.exception_handling import handle_exception
from app.v1.db.database import ARTICLE_COLLECTION

logger = logging.getLogger(__name__)


class ArticleRepository(BaseRepository):
    """
    Initialize repository with article collection name
    """

    def __init__(self):
        super().__init__(ARTICLE_COLLECTION)
        self.logger = logging.getLogger(__name__)

    @handle_exception(
        logger,
        input_identifier_key="doi",
        operation_desc="checking if doi exists in database with doi:",
        include_error_type=True,
    )
    async def article_exists_by_doi(self, doi: str) -> bool:
        """
        Check if an article with the given DOI exists in the database

        Args:
            doi (str): DOI to check

        Returns:
            bool: True if article exists, False otherwise
        """
        try:
            count = await self.count_documents({"doi": doi})
            return count > 0
        except Exception as e:
            error_type = type(e).__name__
            self.logger.error(
                f"Error checking if article exists with doi {doi}: ({error_type}): {e}"
            )
            raise Exception(f"Error checking if article exists with doi {doi}: {e}")

    @handle_exception(
        logger,
        input_identifier_key="doi",
        operation_desc="retrieving multiple articles with doi:",
        include_error_type=True,
    )
    async def get_article_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Retrieve an article by its DOI

        Args:
            doi (str): DOI of the article

        Returns:
            Optional[Dict]: Article data if found, None otherwise
        """
        return await self.find_one({"doi": doi})

    @handle_exception(
        logger,
        input_identifier_key="doi_list",
        operation_desc="retrieving multiple articles with doi list:",
        include_error_type=True,
    )
    async def get_multiple_articles_by_doi(
        self, doi_list: List[str]
    ) -> Optional[List[Dict]]:
        """
        Retrieve an article with a list of DOIs.

        Args:
            doi (List[str]): List of DOIs of articles

        Returns:
            Optional[Dict]: Article data if found, None otherwise
        """
        try:
            return await self.find_many({"doi": {"$in": doi_list}})
        except Exception as e:
            error_type = type(e).__name__
            self.logger.error(
                f"Error retrieving articles with DOIs {doi_list}: ({error_type}): {e}"
            )
            raise Exception(f"Error retrieving articles with DOIs {doi_list}: {e}")

    @handle_exception(
        logger,
        input_identifier_key="field_name",
        operation_desc="retrieving multiple articles with field name filter:",
        include_error_type=True,
    )
    async def get_multiple_articles_with_filter(
        self, field_name: str, match_string: str, exact_match: bool = False
    ) -> Optional[List[Dict]]:
        if exact_match is False:
            query = {field_name: {"$regex": match_string, "$options": "i"}}
            return await self.find_many(query)
        else:
            query = {field_name: match_string}
            return await self.find_many(query)

    @handle_exception(
        logger,
        operation_desc="saving/updating article in database with doi",
        output_identifier_key="doi",
        include_error_type=True,
    )
    async def save_or_update_article(
        self, article_data: Union[Dict, ArticleResponse]
    ) -> str:
        """
        Save an article or update it if it already exists

        Args:
            article_data (Union[Dict, ArticleResponse]): Article data

        Returns:
            str: ID of the inserted or updated article
        """
        # Convert to dict if it's not already
        if hasattr(article_data, "model_dump"):
            article_dict = article_data.model_dump()
        else:
            article_dict = dict(article_data)

        # Ensure we have a DOI
        if "doi" not in article_dict or not article_dict["doi"]:
            raise ValueError("Article must have a DOI")
        doi = article_dict["doi"]

        existing_article = await self.get_article_by_doi(doi)

        if existing_article:
            article_dict["timestamp"] = datetime.utcnow()
            result = await self.update_one({"doi": doi}, article_dict)

        else:
            article_dict["timestamp"] = datetime.utcnow()
            result = await self.insert_one(article_dict)

        if result:
            return article_dict
        else:
            self.logger.error(
                f"Error saving/updating article in database with doi {doi}"
            )
            raise Exception(f"Error saving/updating article in database with doi {doi}")

    @handle_exception(
        logger,
        operation_desc="on saving multiple articles to database.",
        include_error_type=True,
    )
    async def save_downloaded_articles(
        self, articles: List[Union[Dict, ArticleResponse]]
    ) -> List[str]:
        """
        Save multiple downloaded articles

        Args:
            articles (List[Union[Dict, ArticleResponse]]): List of article data

        Returns:
            List[str]: List of inserted document IDs
        """
        saved_articles = []

        for article in articles:
            try:
                result = await self.save_or_update_article(article)
                if result:
                    saved_articles.append(article)
                else:
                    doi = article["doi"]
                    logger.error(
                        f"Error saving single article to database with doi {doi}."
                    )
            except Exception as e:
                doi = article["doi"]
                logger.error(
                    f"Error saving single article to database with doi {doi} with error: {e}"
                )
                # Continue with other articles even if one fails

        if not saved_articles:
            logger.error("Error on saving multiple articles to database.")
            raise Exception("Error on saving multiple articles to database.")

        return saved_articles

    @handle_exception(
        logger, operation_desc="retrieving recent downloads", include_error_type=True
    )
    async def get_recent_downloads(self, limit: int = 10) -> List[Dict]:
        """
        Get the most recently downloaded articles

        Args:
            limit (int): Maximum number of articles to return

        Returns:
            List[Dict]: List of article documents
        """
        return await self.find_many({}, limit=limit, sort=[("timestamp", -1)])

    @handle_exception(
        logger,
        operation_desc="searching articles in database",
        input_identifier_key="query",
        include_error_type=True,
    )
    async def search_articles_in_database(
        self, query: Dict, limit: int = 10, skip: int = 0
    ) -> List[Dict]:
        """
        Search for articles matching the query

        Args:
            query (Dict): Search query
            limit (int): Maximum number of results
            skip (int): Number of results to skip (for pagination)

        Returns:
            List[Dict]: List of matching articles
        """
        return await self.find_many(query, limit=limit, skip=skip)
