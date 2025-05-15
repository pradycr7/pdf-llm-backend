from src.configs import settings
from src.database.mongodb import MongoDB
from src.extractors.pdf_extractor import PDFExtractor
from src.services.s3_service import S3Service
from src.services.llm_service import LLMService
from src.comms.api_server import APIRouterWrapper
from src.comms.app import FastAPIApp
import uvicorn

class Orchestrator:
    def __init__(self):
        self.mongodb = None
        self.s3_service = None
        self.pdf_extractor = None
        self.api_router = None
        self.fastapi_app = None

    def initialize(self):
        # Initialize MongoDB
        MongoDB.initialize(settings.MONGO_URI, settings.DB_NAME)
        self.mongodb = MongoDB
        
        # Initialize PDF Extractor
        self.pdf_extractor = PDFExtractor()

        # Initialize S3 Service
        self.s3_service = S3Service(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            bucket_name=settings.S3_BUCKET_NAME
        )
        
        # Initialize LLM Service
        self.llm_service = LLMService()

        # Initialize API Router
        self.api_router = APIRouterWrapper(self.mongodb, self.s3_service, self.pdf_extractor, self.llm_service)

        # Initialize FastAPI app
        self.fastapi_app = FastAPIApp(self.api_router)
        
        return self

# Create and initialize the orchestrator instance at module level
orchestrator = Orchestrator().initialize()

