"""Publishing service for managing published posts."""

import logging
import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.published_post import PublishedPost
from app.schemas.publishing import PublishedPostCreate

logger = logging.getLogger(__name__)


class PublishingService:
    """Service for publishing operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_published_post(self, data: PublishedPostCreate) -> PublishedPost:
        """Record a manually published post."""
        published_post = PublishedPost(
            article_id=data.article_id,
            site_id=data.site_id,
            wp_post_id=data.wp_post_id,
            url=data.url,
            status="manual",
            published_at=datetime.now(timezone.utc),
        )
        self.db.add(published_post)
        await self.db.commit()
        await self.db.refresh(published_post)
        logger.info(f"Created published post record: {published_post.id}")
        return published_post

    async def get_by_id(self, published_post_id: UUID) -> Optional[PublishedPost]:
        """Get a published post by ID."""
        result = await self.db.execute(
            select(PublishedPost).where(PublishedPost.id == published_post_id)
        )
        return result.scalar_one_or_none()

    async def get_by_article(
        self,
        article_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[PublishedPost], int]:
        """Get published posts for an article with pagination."""
        query = select(PublishedPost).where(PublishedPost.article_id == article_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and order
        query = query.order_by(PublishedPost.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        posts = result.scalars().all()

        return list(posts), total

    async def get_by_site(
        self,
        site_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[PublishedPost], int]:
        """Get published posts for a site with pagination."""
        query = select(PublishedPost).where(PublishedPost.site_id == site_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and order
        query = query.order_by(PublishedPost.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        posts = result.scalars().all()

        return list(posts), total


def clean_html_for_wordpress(html_content: str) -> str:
    """Clean HTML content for WordPress publishing.
    
    Removes potentially dangerous elements like script tags, on* event handlers,
    and other elements that could cause security issues or layout problems.
    """
    if not html_content:
        return ""
    
    # Remove script tags and their content
    html_content = re.sub(r'<script\b[^>]*>[\s\S]*?</script>', '', html_content, flags=re.IGNORECASE)
    
    # Remove style tags and their content (optional - WordPress often handles CSS)
    html_content = re.sub(r'<style\b[^>]*>[\s\S]*?</style>', '', html_content, flags=re.IGNORECASE)
    
    # Remove on* event handlers
    html_content = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'\s+on\w+\s*=\s*[^\s>]+', '', html_content, flags=re.IGNORECASE)
    
    # Remove javascript: URLs
    html_content = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href=""', html_content, flags=re.IGNORECASE)
    
    # Remove iframe tags (commonly used for embedding potentially harmful content)
    html_content = re.sub(r'<iframe\b[^>]*>[\s\S]*?</iframe>', '', html_content, flags=re.IGNORECASE)
    
    # Remove object and embed tags
    html_content = re.sub(r'<object\b[^>]*>[\s\S]*?</object>', '', html_content, flags=re.IGNORECASE)
    html_content = re.sub(r'<embed\b[^>]*/?>', '', html_content, flags=re.IGNORECASE)
    
    return html_content.strip()


def convert_html_to_markdown(html_content: str) -> str:
    """Convert HTML content to Markdown format.
    
    Simple conversion for basic HTML elements commonly used in articles.
    For complex conversions, consider using a library like html2text.
    """
    if not html_content:
        return ""
    
    content = html_content
    
    # Convert headers
    content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<h5[^>]*>(.*?)</h5>', r'##### \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<h6[^>]*>(.*?)</h6>', r'###### \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Convert bold and italic
    content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Convert links
    content = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Convert images
    content = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)', content, flags=re.IGNORECASE)
    content = re.sub(r'<img[^>]*alt=["\']([^"\']*)["\'][^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![\1](\2)', content, flags=re.IGNORECASE)
    content = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![](\1)', content, flags=re.IGNORECASE)
    
    # Convert lists
    content = re.sub(r'<ul[^>]*>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</ul>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'<ol[^>]*>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'</ol>', '\n', content, flags=re.IGNORECASE)
    content = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Convert paragraphs
    content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Convert line breaks
    content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
    
    # Convert blockquotes
    content = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'> \1\n', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Convert code blocks
    content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<pre[^>]*>(.*?)</pre>', r'```\n\1\n```', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Clean up extra whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Decode common HTML entities
    content = content.replace('&nbsp;', ' ')
    content = content.replace('&amp;', '&')
    content = content.replace('&lt;', '<')
    content = content.replace('&gt;', '>')
    content = content.replace('&quot;', '"')
    content = content.replace('&#39;', "'")
    
    return content.strip()
