from motor.motor_asyncio import AsyncIOMotorClient
from src.utils.logger import app_logger
from src.configs.settings import MONGO_URI, DB_NAME

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    def initialize(cls, uri, db_name):
        # Use the same variable names as declared at class level
        cls.client = AsyncIOMotorClient(uri)
        cls.db = cls.client[db_name]
        app_logger.info(f"MongoDB initialized DB name: {db_name}")
        
    @classmethod
    def get_documents_collection(cls):
        if cls.db is None:
            raise ValueError("MongoDB not initialized. Call MongoDB.initialize() first.")
        return cls.db.document_details  # Changed from document_details to documents for consistency
