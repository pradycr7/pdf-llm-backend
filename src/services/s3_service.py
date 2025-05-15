import boto3
from bson import ObjectId
from fastapi import UploadFile, HTTPException
from botocore.exceptions import NoCredentialsError
from datetime import datetime
import traceback
from src.configs.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME

class S3Service:
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, 
            region_name=None, bucket_name=None):
        self.bucket_name = str(bucket_name or S3_BUCKET_NAME) if (bucket_name or S3_BUCKET_NAME) is not None else None
        self.region_name = str(region_name or AWS_REGION) if (region_name or AWS_REGION) is not None else None
        if not self.bucket_name:
            raise ValueError("S3 bucket name must be provided")
            
        # Initialize the S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id or AWS_ACCESS_KEY_ID,
            aws_secret_access_key=aws_secret_access_key or AWS_SECRET_ACCESS_KEY,
            region_name=region_name or AWS_REGION
        )




    async def upload_file_to_s3(self, file: UploadFile, doc_id: str) -> str:
        """Upload file to S3 and return browser-accessible s3 URL"""
        try:
            # Ensure that doc_id is valid
            if not ObjectId.is_valid(doc_id):
                raise HTTPException(status_code=400, detail="Invalid ObjectId format")

            s3_key = f"documents/{doc_id}.pdf"
            content = await file.read()

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content
            )

            # Construct the browser-accessible URL from S3
            s3_url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{s3_key}"

            # Return the S3 URL
            return s3_url
            
        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Upload to S3 failed: {str(e)}")


