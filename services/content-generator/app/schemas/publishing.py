"""Schemas for Publishing Service."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class PublishedPostCreate(BaseModel):
    """Schema for creating a published post record."""

    article_id: UUID
    site_id: UUID
    url: Optional[str] = Field(None, max_length=500)
    wp_post_id: Optional[int] = None


class PublishedPostResponse(BaseModel):
    """Schema for published post response."""

    id: UUID
    article_id: Optional[UUID] = None
    site_id: Optional[UUID] = None
    wp_post_id: Optional[int] = None
    url: Optional[str] = None
    status: str
    published_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleExportResponse(BaseModel):
    """Schema for article export response."""

    id: UUID
    title: str
    format: str  # 'html' | 'markdown'
    content: str
    word_count: Optional[int] = None
