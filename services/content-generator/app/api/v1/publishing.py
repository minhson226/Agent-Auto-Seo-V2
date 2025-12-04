"""Publishing API endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.publishing import (
    ArticleExportResponse,
    PublishedPostCreate,
    PublishedPostResponse,
)
from app.services.article_service import ArticleService
from app.services.publishing_service import (
    PublishingService,
    clean_html_for_wordpress,
    convert_html_to_markdown,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Publishing"])


@router.get(
    "/articles/{article_id}/export",
    response_model=ArticleExportResponse,
)
async def export_article(
    article_id: UUID,
    format: str = Query("html", pattern="^(html|markdown)$"),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export an article in HTML or Markdown format.
    
    - HTML format: Returns clean HTML ready for WordPress (script tags removed, etc.)
    - Markdown format: Returns content converted to Markdown for other platforms
    
    Use this endpoint to get content that can be copied and pasted into a CMS.
    """
    article_service = ArticleService(db)
    article = await article_service.get_by_id(article_id)
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    
    if not article.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article has no content to export",
        )
    
    if format == "html":
        # Clean HTML for WordPress
        exported_content = clean_html_for_wordpress(article.content)
    else:
        # Convert to Markdown
        exported_content = convert_html_to_markdown(article.content)
    
    return ArticleExportResponse(
        id=article.id,
        title=article.title,
        format=format,
        content=exported_content,
        word_count=article.word_count,
    )


@router.post(
    "/published-posts",
    response_model=PublishedPostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_published_post(
    data: PublishedPostCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a manually published post.
    
    Use this endpoint to track articles that have been manually copy-pasted
    to WordPress or other platforms. This creates a record linking the
    original article to the published URL.
    
    Request body:
    - article_id: The ID of the article that was published
    - site_id: The ID of the site where the article was published
    - url: (optional) The public URL of the published post
    - wp_post_id: (optional) The WordPress post ID if published to WordPress
    """
    # Verify article exists
    article_service = ArticleService(db)
    article = await article_service.get_by_id(data.article_id)
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    
    # Create published post record
    publishing_service = PublishingService(db)
    published_post = await publishing_service.create_published_post(data)
    
    return PublishedPostResponse(
        id=published_post.id,
        article_id=published_post.article_id,
        site_id=published_post.site_id,
        wp_post_id=published_post.wp_post_id,
        url=published_post.url,
        status=published_post.status,
        published_at=published_post.published_at,
        created_at=published_post.created_at,
    )


@router.get(
    "/published-posts/{published_post_id}",
    response_model=PublishedPostResponse,
)
async def get_published_post(
    published_post_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a published post record by ID."""
    publishing_service = PublishingService(db)
    published_post = await publishing_service.get_by_id(published_post_id)
    
    if not published_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published post not found",
        )
    
    return PublishedPostResponse(
        id=published_post.id,
        article_id=published_post.article_id,
        site_id=published_post.site_id,
        wp_post_id=published_post.wp_post_id,
        url=published_post.url,
        status=published_post.status,
        published_at=published_post.published_at,
        created_at=published_post.created_at,
    )


@router.get(
    "/articles/{article_id}/published-posts",
    response_model=list[PublishedPostResponse],
)
async def list_published_posts_by_article(
    article_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all published post records for an article."""
    publishing_service = PublishingService(db)
    posts, _ = await publishing_service.get_by_article(
        article_id=article_id,
        page=page,
        page_size=page_size,
    )
    
    return [
        PublishedPostResponse(
            id=post.id,
            article_id=post.article_id,
            site_id=post.site_id,
            wp_post_id=post.wp_post_id,
            url=post.url,
            status=post.status,
            published_at=post.published_at,
            created_at=post.created_at,
        )
        for post in posts
    ]
