"""User model."""

import os
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, JSON, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# Use schema for PostgreSQL, skip for SQLite (testing)
def get_table_args():
    """Get table args with schema if not using SQLite."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" in db_url:
        return {}
    return {"schema": "autoseo"}


# Use JSONB for PostgreSQL, JSON for SQLite
def get_json_type():
    """Get JSON type based on database."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" in db_url:
        return JSON
    return JSONB


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", get_json_type(), default=dict, server_default="{}"
    )

    # Relationships
    owned_workspaces = relationship(
        "Workspace", back_populates="owner", cascade="all, delete-orphan"
    )
    workspace_memberships = relationship(
        "WorkspaceMember", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
