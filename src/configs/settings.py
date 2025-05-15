import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# AWS S3 configuration
AWS_ACCESS_KEY_ID = os.getenv("CUSTOM_AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("CUSTOM_AWS_SECRET_KEY")
AWS_REGION = os.getenv("CUSTOM_AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# LLM configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY must be set in the environment variables.")

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME")
if not GEMINI_MODEL_NAME:
    raise ValueError("GEMINI_MODEL_NAME must be set in the environment variables.")

# JWT configuration
# Get JWT settings from environment variables
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
try:
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
except ValueError:
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Validate required environment variables
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable is not set")


