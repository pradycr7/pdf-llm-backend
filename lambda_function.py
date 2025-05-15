# AWS Lambda Entry-point
# This file is used to run the FastAPI application on AWS Lambda.

from mangum import Mangum
from src.orchestrator import Orchestrator

orchestrator = Orchestrator().initialize()
# The Mangum handler wraps the FastAPI app for AWS Lambda compatibility
handler = Mangum(orchestrator.fastapi_app.app)
