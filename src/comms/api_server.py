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
        self._setup_document_retrieval_routes()
        self._setup_llm_processing_routes()
        self._setup_auth_routes()
    
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

    def _setup_document_retrieval_routes(self):
        """Routes for document retrieval and listing"""
        @self.router.get('/documents/{doc_id}')
        @timing_decorator(log_level="info", description="Get document by ID")
        async def get_document(doc_id: str = Path(..., description="The ID of the document to retrieve")):
            try:
                # Convert the doc_id from string to ObjectId
                object_id = ObjectId(doc_id)
            except Exception as e:
                app_logger.error(f"LLM generation failed for document {doc_id}: {str(e)}", exc_info=True)
                raise HTTPException(status_code=400, detail="Invalid ObjectId format")

            # Query the document using ObjectId
            document = await self.mongodb.get_documents_collection().find_one({"_id": object_id})
            
            if not document:
                app_logger.error(f"Document not found for ID: {doc_id}")
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Prepare the response content
            response = {
                "doc_id": str(document["_id"]),
                "filename": document["filename"],
                "upload_time": document["upload_time"].isoformat(),
                "extracted_text": document["extracted_text"]
            }
            
            return JSONResponse(content=response)
        
        @self.router.get('/documents')
        @timing_decorator(log_level="info", description="Get all documents with pagination")
        async def get_documents(
            page: int = Query(1, ge=1, description="Page number, starting from 1"),
            limit: int = Query(10, ge=1, le=100, description="Number of documents per page")
        ):
            # Calculate skip value based on page and limit
            skip = (page - 1) * limit
            
            # Get total document count for pagination metadata
            total_docs = await self.mongodb.get_documents_collection().count_documents({})
            
            # Get documents for the requested page with limit
            cursor = self.mongodb.get_documents_collection().find({}) \
                        .sort("upload_time", -1) \
                        .skip(skip) \
                        .limit(limit)
            
            # Convert cursor to list of documents
            documents = []
            async for doc in cursor:
                documents.append({
                    "doc_id": str(doc["_id"]),
                    "filename": doc["filename"],
                    "upload_time": doc["upload_time"].isoformat(),
                    "text_preview": doc.get("extracted_text", "")[:100] + "..." if doc.get("extracted_text") else ""
                })
            
            # Calculate total pages
            total_pages = (total_docs + limit - 1) // limit
            
            # Create response with documents and pagination metadata
            response = {
                "documents": documents,
                "pagination": {
                    "total": total_docs,
                    "page": page,
                    "limit": limit,
                    "pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
            return JSONResponse(content=response)

    def _setup_llm_processing_routes(self):
        """Routes for LLM-based document processing (summarization and querying)"""
        @self.router.post('/summarize/{doc_id}')
        @timing_decorator(log_level="info", description="Summarize document")
        async def summarize_document(
            doc_id: str = Path(..., description="Document ID to summarize"),
            token_payload: dict = Depends(self.jwt_auth.get_token_verify_dependency())
        ):
            try:
                object_id = ObjectId(doc_id)
            except Exception as e:
                app_logger.error(f"LLM generation failed for document {doc_id}: {str(e)}", exc_info=True)
                raise HTTPException(status_code=400, detail="Invalid ObjectId format")
            
            document = await self.mongodb.get_documents_collection().find_one({"_id": object_id})
            if not document:
                app_logger.error(f"Document not found for ID: {doc_id}")
                raise HTTPException(status_code=404, detail="Document not found")
            
            pdf_content = document.get("extracted_text", "")
            if not pdf_content:
                app_logger.error(f"Document has no extracted text for ID: {doc_id}")
                raise HTTPException(status_code=400, detail="Document has no extracted text")
            
            prompt = "Summarize the following content in 2 sentences:\n\n"
            final_prompt = f"{prompt}{pdf_content}"
            
            try:
                response = await self.llm_service.generate_content(final_prompt)
                
                return JSONResponse(content={
                    "doc_id": doc_id,
                    "summary": response
                })
            except Exception as e:
                app_logger.error(f"Summarization failed for document {doc_id}: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

        @self.router.post('/query/{doc_id}/{question:path}')
        @timing_decorator(log_level="info", description="Query document and get answer using LLM")
        async def query_document(
            request: Request,
            doc_id: str = Path(...),
            question: str = Path(...)
        ):
            # Get the full path and query components
            path_part = request.url.path
            query_part = request.url.query
            
            # Extract the raw question from the URL path
            prefix = f"/query/{doc_id}/"
            idx = path_part.find(prefix) + len(prefix)
            raw_question = path_part[idx:]
            
            # If there's a query part, it means there was a question mark in the original question
            if query_part:
                raw_question += "?" + query_part
            
            # URL decode to get the actual question text
            full_question = urllib.parse.unquote(raw_question)
                
            try:
                object_id = ObjectId(doc_id)
            except Exception as e:
                app_logger.error(f"LLM generation failed for document {doc_id}: {str(e)}", exc_info=True)
                raise HTTPException(status_code=400, detail="Invalid ObjectId format")
            
            document = await self.mongodb.get_documents_collection().find_one({"_id": object_id})
            if not document:
                app_logger.error(f"Document not found for ID: {doc_id}")
                raise HTTPException(status_code=404, detail="Document not found")
            
            pdf_content = document.get("extracted_text", "")
            if not pdf_content:
                app_logger.error(f"Document has no extracted text for ID: {doc_id}")
                raise HTTPException(status_code=400, detail="Document has no extracted text")
            
            prompt = f"Answer the following question based on the document content:\n\nQuestion: {full_question}\n\nDocument:"
            final_prompt = f"{prompt}\n\n{pdf_content}"
            
            try:
                response = await self.llm_service.generate_content(final_prompt)
                
                return JSONResponse(content={
                    "doc_id": doc_id,
                    "question": full_question,
                    "answer": response
                })
            except Exception as e:
                app_logger.error(f"Query failed for document {doc_id}: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    def _setup_auth_routes(self):
        """Authentication and token-related routes"""
        @self.router.post("/generate-token")
        @timing_decorator(log_level="info", description="Generate JWT token")
        async def generate_token():
            """Generate a JWT token without requiring API key"""
            return await self.jwt_auth.generate_token()

