from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    notebook_id: str = Field(..., min_length=1)
    tags: Optional[List[str]] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be blank")
        return v.strip()

class SourceCreate(BaseModel):
    url: str = Field(..., min_length=1)
    title: Optional[str] = None
    notebook_id: str
    source_type: str = "web"

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

class SettingsUpdate(BaseModel):
    key: str = Field(..., min_length=1)
    value: str
