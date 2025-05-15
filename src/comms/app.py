from fastapi import FastAPI

class FastAPIApp:
    def __init__(self, api_router):
        self.app = FastAPI(
            title="PDF Summarizer API",
            description="API for uploading and extracting text from PDFs",
            version="1.0.0"
        )
        self.app.include_router(api_router.router, tags=["documents"])
        self._setup_root()

    def _setup_root(self):
        @self.app.get("/")
        async def root():
            return {"message": "PDF Summarizer API is running"}
