"""Workspace model."""

import os
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, func
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


def get_users_foreign_key():
    """Get foreign key reference for users with schema qualification."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" in db_url:
        return "users.id"
    return "autoseo.users.id"


def get_workspaces_foreign_key():
    """Get foreign key reference for workspaces with schema qualification."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" in db_url:
        return "workspaces.id"
    return "autoseo.workspaces.id"


class Workspace(Base):
    """Workspace model for multi-tenant organization."""

    __tablename__ = "workspaces"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(get_users_foreign_key(), ondelete="CASCADE"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    settings: Mapped[dict] = mapped_column(get_json_type(), default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    owner = relationship("User", back_populates="owned_workspaces")
    members = relationship(
        "WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan"
    )
    sites = relationship("Site", back_populates="workspace", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceMember(Base):
    """Workspace member junction table."""

    __tablename__ = "workspace_members"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_workspaces_foreign_key(), ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_users_foreign_key(), ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), default="member")
    permissions: Mapped[list] = mapped_column(get_json_type(), default=list, server_default="[]")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspace_memberships")
