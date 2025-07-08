from typing import Dict, List, Optional, Union
import logging
from app.v1.db.database import get_database

logger = logging.getLogger(__name__)


class BaseRepository:
    """
    Base repository class for MongoDB operations
    Provides common database operations
    """

    def __init__(self, collection_name: str):
        """
        Initialize repository with collection name

        Args:
            collection_name (str): Name of the MongoDB collection
        """
        self.collection_name = collection_name
        self._collection = None

    async def _get_collection(self):
        """
        Get a reference to the MongoDB collection

        Returns:
            AsyncIOMotorCollection: MongoDB collection
        """
        if self._collection is None:
            # Import here to avoid circular imports
            database = await get_database()
            self._collection = database[self.collection_name]
        return self._collection

    async def insert_one(self, document: Dict) -> str:
        """
        Insert a single document into the collection

        Args:
            document (Dict): Document to insert

        Returns:
            str: ID of the inserted document
        """
        try:
            collection = await self._get_collection()
            result = await collection.insert_one(document)
            logger.info(f"Document inserted with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error inserting document into {self.collection_name}: {e}")
            raise

    async def insert_many(self, documents: List[Dict]) -> List[str]:
        """
        Insert multiple documents into the collection

        Args:
            documents (List[Dict]): List of documents to insert

        Returns:
            List[str]: List of inserted document IDs
        """
        try:
            collection = await self._get_collection()
            result = await collection.insert_many(documents)
            inserted_ids = [str(id) for id in result.inserted_ids]
            logger.info(
                f"Inserted {len(inserted_ids)} documents into {self.collection_name}"
            )
            return inserted_ids
        except Exception as e:
            logger.error(f"Error inserting documents into {self.collection_name}: {e}")
            raise

    async def find_one(self, query: Dict) -> Optional[Dict]:
        """
        Find a single document matching the query

        Args:
            query (Dict): Query to find the document

        Returns:
            Optional[Dict]: Matching document or None
        """
        try:
            collection = await self._get_collection()
            document = await collection.find_one(query)
            return document
        except Exception as e:
            logger.error(f"Error finding document in {self.collection_name}: {e}")
            raise

    async def find_many(
        self, query: Dict, limit: int = 0, skip: int = 0, sort: Optional[List] = None
    ) -> List[Dict]:
        """
        Find multiple documents matching the query

        Args:
            query (Dict): Query to find documents
            limit (int): Maximum number of documents to return (0 for all)
            skip (int): Number of documents to skip
            sort (Optional[List]): Sort specification

        Returns:
            List[Dict]: List of matching documents
        """
        try:
            collection = await self._get_collection()
            cursor = collection.find(query)

            # Apply pagination
            if skip > 0:
                cursor = cursor.skip(skip)
            if limit > 0:
                cursor = cursor.limit(limit)

            # Apply sorting
            if sort:
                cursor = cursor.sort(sort)

            # Convert cursor to list
            documents = await cursor.to_list(length=limit if limit > 0 else None)
            return documents
        except Exception as e:
            logger.error(f"Error finding documents in {self.collection_name}: {e}")
            raise

    async def update_one(
        self, query: Dict, update_data: Dict, upsert: bool = False
    ) -> Dict[str, Union[int, bool, str, None]]:
        """
        Update a single document matching the query

        Args:
            query (Dict): Query to find the document to update
            update_data (Dict): Data to update
            upsert (bool): Insert document if it doesn't exist

        Returns:
            Dict with modified_count, matched_count, and upserted_id if applicable
        """
        try:
            collection = await self._get_collection()
            # Use $set operator if not already included
            if not any(key.startswith("$") for key in update_data.keys()):
                update_data = {"$set": update_data}

            result = await collection.update_one(query, update_data, upsert=upsert)

            return {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": str(result.upserted_id) if result.upserted_id else None,
            }
        except Exception as e:
            logger.error(f"Error updating document in {self.collection_name}: {e}")
            raise

    async def update_many(
        self, query: Dict, update_data: Dict, upsert: bool = False
    ) -> Dict[str, int]:
        """
        Update multiple documents matching the query

        Args:
            query (Dict): Query to find documents to update
            update_data (Dict): Data to update
            upsert (bool): Insert documents if they don't exist

        Returns:
            Dict with modified_count and matched_count
        """
        try:
            collection = await self._get_collection()
            # Use $set operator if not already included
            if not any(key.startswith("$") for key in update_data.keys()):
                update_data = {"$set": update_data}

            result = await collection.update_many(query, update_data, upsert=upsert)

            return {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
            }
        except Exception as e:
            logger.error(f"Error updating documents in {self.collection_name}: {e}")
            raise

    async def delete_one(self, query: Dict) -> int:
        """
        Delete a single document matching the query

        Args:
            query (Dict): Query to find the document to delete

        Returns:
            int: Number of deleted documents
        """
        try:
            collection = await self._get_collection()
            result = await collection.delete_one(query)
            return result.deleted_count
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"Error deleting document from {self.collection_name}: ({error_type}): {e}"
            )
            raise Exception(
                f"Error deleting document from {self.collection_name}: {str(e)}"
            )

    async def delete_many(self, query: Dict) -> int:
        """
        Delete multiple documents matching the query

        Args:
            query (Dict): Query to find documents to delete

        Returns:
            int: Number of deleted documents
        """
        try:
            collection = await self._get_collection()
            result = await collection.delete_many(query)
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting documents from {self.collection_name}: {e}")
            raise

    async def count_documents(self, query: Dict) -> int:
        """
        Count documents matching the query

        Args:
            query (Dict): Query to count documents

        Returns:
            int: Number of matching documents
        """
        try:
            collection = await self._get_collection()
            return await collection.count_documents(query)
        except Exception as e:
            logger.error(f"Error counting documents in {self.collection_name}: {e}")
            raise
