from fastapi import APIRouter, UploadFile, File, HTTPException, Path, Request, Query, Depends
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime
from src.utils.auth import JWTAuth
from src.utils.validate_pdf import PDFValidator
from src.utils.logger import app_logger
from src.utils.timing_decorator import timing_decorator
import urllib.parse

class APIRouterWrapper:
    def __init__(self, mongodb, s3_service, pdf_extractor, llm_service):
        self.router = APIRouter()
        self.mongodb = mongodb
        self.s3_service = s3_service
        self.pdf_extractor = pdf_extractor
        self.llm_service = llm_service
        self.jwt_auth = JWTAuth()
        self.pdf_validator = PDFValidator(min_file_size=1024)
        self._setup_routes()

    def _setup_routes(self):
        """Main route setup method that delegates to feature-specific methods"""
        self._setup_document_upload_routes()
        
    
    def _setup_document_upload_routes(self):
        """Routes for document upload functionality"""
        @self.router.post('/upload')
        @timing_decorator(log_level="info", description="Upload PDF and extract text")
        async def upload_pdf(file: UploadFile = File(...)):
            app_logger.info(f"Processing upload of {file.filename}")
            # Validate PDF
            is_valid, error_message = await self.pdf_validator.is_valid_upload(file)
            if not is_valid:
                app_logger.warning(f"Invalid PDF rejected: {file.filename} - {error_message}")
                raise HTTPException(status_code=400, detail=error_message)

            try:
                # Step 1: Create initial document
                initial_doc = {
                    "filename": file.filename,
                    "upload_time": datetime.utcnow(),
                    "extracted_text": "",
                    "s3_uri": "",
                }

                # Step 2: Insert the document to get ObjectId
                result = await self.mongodb.get_documents_collection().insert_one(initial_doc)
                doc_id = result.inserted_id
                app_logger.info(f"Initial document created with ObjectId: {doc_id}")

                # Step 3: Upload to S3
                s3_url = await self.s3_service.upload_file_to_s3(file, doc_id)
                app_logger.info(f"File uploaded to S3 with URL: {s3_url}")

                # Step 4: Extract text from PDF
                file.file.seek(0)
                extracted_text = await self.pdf_extractor.extract_text(file)

                # Step 5: Update MongoDB with extracted text and S3 URL
                updated_doc_data = {
                    "extracted_text": extracted_text,
                    "s3_uri": s3_url,
                }

                # Step 6: Update the document in MongoDB
                update_result = await self.mongodb.get_documents_collection().update_one(
                    {"_id": doc_id},
                    {"$set": updated_doc_data}
                )
                if update_result.modified_count == 0:
                    raise HTTPException(status_code=500, detail="Failed to update document in database.")

                # Step 7: Retrieve the document and convert ObjectId to string
                final_doc = await self.mongodb.get_documents_collection().find_one({"_id": doc_id})
                final_doc["_id"] = str(final_doc["_id"])

                response = {
                    "doc_id": final_doc["_id"],
                    "message": "PDF File uploaded to s3 and text extracted successfully",
                }
                
                return JSONResponse(content=response)

            except Exception as e:
                app_logger.error(f"Error during upload process: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Upload to s3 failed: {str(e)}")

    