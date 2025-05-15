from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Document(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    filename: str
    upload_time: datetime
    extracted_text: str
    s3_uri: str
