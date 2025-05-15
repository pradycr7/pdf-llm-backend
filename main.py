# Local Development Entry-point
# This file is used to run the FastAPI application locally.

import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.orchestrator:orchestrator.fastapi_app.app", 
                host="0.0.0.0", 
                port=8000, 
                reload=True)
