"""Published Post model for tracking published articles."""

import os
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def is_sqlite():
    """Check if using SQLite database."""
    db_url = os.environ.get("DATABASE_URL", "")
    return "sqlite" in db_url


def get_table_args():
    """Get table args with schema if not using SQLite."""
    if is_sqlite():
        return {}
    return {"schema": "autoseo"}


class PublishedPost(Base):
    """Model for tracking published articles to external sites."""

    __tablename__ = "published_posts"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # article_id and site_id without FK constraint for SQLite test compatibility
    # In production with PostgreSQL, the FK is enforced by migration
    article_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    site_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    wp_post_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="manual"
    )  # 'manual' | 'auto' | 'pending'
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
