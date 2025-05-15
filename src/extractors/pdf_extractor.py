import pdfplumber
from fastapi import UploadFile

class PDFExtractor:
    def __init__(self):
        pass

    async def extract_text(self, file: UploadFile) -> str:
        """Extract text from a PDF file using pdfplumber with layout preservation"""
        with pdfplumber.open(file.file) as pdf:
            text = ''
            for page in pdf.pages:
                # Extract text with layout
                page_text = page.extract_text(layout=True)
                if page_text:
                    text += page_text + '\n\n'
        return text

# Example usage:
# extractor = PDFExtractor()
# extracted_text = await extractor.extract_text(uploaded_file)
