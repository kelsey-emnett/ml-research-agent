from app.v1.repositories.base import BaseRepository
from app.v1.schemas.articles import ArticleResponse
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime

from app.v1.db.database import ARTICLE_COLLECTION

logger = logging.getLogger(__name__)


class ArticleRepository(BaseRepository):
    """
    Initialize repository with article collection name
    """

    def __init__(self):
        super().__init__(ARTICLE_COLLECTION)
        self.logger = logging.getLogger(__name__)

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

    async def get_article_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Retrieve an article by its DOI

        Args:
            doi (str): DOI of the article

        Returns:
            Optional[Dict]: Article data if found, None otherwise
        """
        try:
            return await self.find_one({"doi": doi})
        except Exception as e:
            error_type = type(e).__name__
            self.logger.error(
                f"Error retrieving article using doi with doi {doi}: ({error_type}): {e}"
            )
            raise Exception(f"Error retrieving article using doi with doi {doi}: {e}")

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

    async def get_multiple_articles_with_filter(
        self, field_name: str, match_string: str, exact_match: bool = False
    ) -> Optional[List[Dict]]:
        try:
            if exact_match is False:
                query = {field_name: {"$regex": match_string, "$options": "i"}}
                return await self.find_many(query)
            else:
                query = {field_name: match_string}
                return await self.find_many(query)
        except Exception as e:
            error_type = type(e).__name__
            self.logger.error(
                f"Error retrieving articles with field name {field_name} and string {match_string}: ({error_type}): {e}"
            )
            raise Exception(
                f"Error retrieving articles with field name {field_name} and string {match_string}: {e}"
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
        try:
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
                raise Exception(
                    f"Error saving/updating article in database with doi {doi}"
                )
        except Exception as e:
            error_type = type(e).__name__
            self.logger.error(
                f"Error saving/updating article in database with doi {article_data["doi"]} ({error_type}): {e}"
            )
            raise Exception(
                f"Error saving/updating article in database with doi {article_data["doi"]}: {e}"
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
                    logger.error(
                        f"Error saving single article to database with doi {article["doi"]}."
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

    async def get_recent_downloads(self, limit: int = 10) -> List[Dict]:
        """
        Get the most recently downloaded articles

        Args:
            limit (int): Maximum number of articles to return

        Returns:
            List[Dict]: List of article documents
        """
        try:
            return await self.find_many({}, limit=limit, sort=[("timestamp", -1)])
        except Exception as e:
            error_type = type(e).__name__
            self.logger.error(f"Error retrieving recent downloads: ({error_type}): {e}")
            raise Exception(f"Error retrieving recent downloads: {e}")

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
        try:
            return await self.find_many(query, limit=limit, skip=skip)
        except Exception as e:
            error_type = type(e).__name__
            self.logger.error(
                f"Error searching articles in database: ({error_type}): {e}"
            )
            raise Exception(f"Error searching articles in database: {e}")
