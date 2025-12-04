"""Internal Link Map model for tracking internal links."""

import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
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


class InternalLinkMap(Base):
    """Model for tracking internal links between published posts."""

    __tablename__ = "internal_link_map"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # from_post_id and to_post_id without FK constraint for SQLite test compatibility
    # In production with PostgreSQL, the FK is enforced by migration
    from_post_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    to_post_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    anchor_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    similarity_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    link_type: Mapped[str] = mapped_column(
        String(50), default="string_match"
    )  # 'string_match' | 'semantic'
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    applied_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
