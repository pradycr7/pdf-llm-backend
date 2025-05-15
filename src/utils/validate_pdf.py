import os
import pdfplumber
import tempfile
from typing import Tuple
from fastapi import UploadFile

class PDFValidator:
    """Class for validating PDF files and ensuring they meet criteria for processing."""
    
    def __init__(self, min_file_size=1024):
        """
        Initialize the PDF validator.
        
        Args:
            min_file_size: Minimum acceptable file size in bytes (default 1KB)
        """
        self.min_file_size = min_file_size
    
    def is_valid(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if a PDF file is properly formatted and readable.
        
        Args:
            file_path: Path to the PDF file to validate
            
        Returns:
            tuple: (bool, str) True if the PDF is valid, False otherwise, and error message
        """
        try:
            # Check if file exists and is a file
            if not os.path.isfile(file_path):
                return False, "File does not exist or is not a file"
            
            # Check file size (must be > minimum size)
            if os.path.getsize(file_path) < self.min_file_size:
                return False, f"File size is too small (less than {self.min_file_size} bytes)"
            
            # Validate PDF structure (header and EOF)
            valid_structure = self._check_pdf_structure(file_path)
            if not valid_structure:
                return False, "PDF structure invalid: missing header or EOF marker"
            
            # Validate PDF content is readable
            content_valid, content_msg = self._check_pdf_content(file_path)
            if not content_valid:
                return False, content_msg
                
        except Exception as e:
            return False, f"PDF validation failed: {str(e)}"
        
        return True, "PDF is valid"
    
    def _check_pdf_structure(self, file_path: str) -> bool:
        """Check if the file has proper PDF structure with header and EOF marker."""
        try:
            with open(file_path, 'rb') as f:
                # Check for PDF header
                header = f.read(5)
                if header != b'%PDF-':
                    return False
                
                # Check for EOF marker in the last 1024 bytes
                f.seek(-1024, os.SEEK_END)
                tail = f.read(1024)
                if b'%%EOF' not in tail:
                    return False
            
            return True
        except Exception:
            return False
    
    def _check_pdf_content(self, file_path: str) -> Tuple[bool, str]:
        """Check if the PDF content is readable using pdfplumber and not encrypted or blank."""
        # First check if PDF is encrypted using pypdf
        from pypdf import PdfReader
        
        try:
            reader = PdfReader(file_path)
            if reader.is_encrypted:
                return False, "PDF is encrypted and cannot be processed"
        except Exception as e:
            # If pypdf fails, continue with pdfplumber checks
            pass
        try:
            with pdfplumber.open(file_path) as pdf:
                
                # Check if PDF has at least one page
                if len(pdf.pages) == 0:
                    return False, "PDF has no pages"
                
                # Try to extract text from first page to verify content is readable
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                if text is None or text.strip() == "":
                    return False, "PDF page is blank or contains no extractable text"
            
            return True, "PDF content is valid"
        except Exception as e:
            return False, f"PDF content validation failed: {str(e)}"
    
    async def is_valid_upload(self, upload_file: UploadFile) -> Tuple[bool, str]:
        """
        Validate if an uploaded file is a valid PDF.
        
        Args:
            upload_file: FastAPI UploadFile object
            
        Returns:
            tuple: (bool, str) True if the uploaded file is a valid PDF, False otherwise, and error message
        """
        if not upload_file.filename.endswith('.pdf'):
            return False, "File extension is not .pdf"
        
        # Create temporary file to validate
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            content = await upload_file.read()
            temp.write(content)
            temp_path = temp.name
        
        # Reset file pointer for future operations
        await upload_file.seek(0)
        
        # Use the file validation method
        result, message = self.is_valid(temp_path)
        
        # Clean up
        os.unlink(temp_path)
        return result, message
