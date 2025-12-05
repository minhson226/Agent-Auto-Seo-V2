"""Data models for internal linking."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class InternalLinkOpportunity:
    """Represents a potential internal link opportunity."""

    from_article_id: UUID
    to_article_id: UUID
    keyword: str
    position: Optional[int] = None  # Character position in content
    context: Optional[str] = None  # Surrounding text context
    similarity_score: Optional[float] = None


@dataclass
class RelatedArticle:
    """Represents a semantically related article."""

    article_id: UUID
    title: str
    url: Optional[str] = None
    similarity: float = 0.0
    embedding: Optional[List[float]] = None
    target_keywords: Optional[List[str]] = None


@dataclass
class LinkSuggestion:
    """Represents a suggested internal link with context."""

    source_article_id: UUID
    target_article_id: UUID
    target_url: str
    anchor_text: str
    original_sentence: str
    rewritten_sentence: Optional[str] = None
    similarity_score: float = 0.0
    link_type: str = "string_match"  # 'string_match' | 'semantic'


@dataclass
class InternalLinkMap:
    """Represents an entry in the internal link map."""

    id: UUID
    from_post_id: UUID
    to_post_id: UUID
    anchor_text: str
    similarity_score: float
    created_at: Optional[str] = None
