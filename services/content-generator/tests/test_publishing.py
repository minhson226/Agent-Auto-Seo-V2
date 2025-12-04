"""Tests for publishing API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import text


class TestExportArticle:
    """Tests for article export functionality."""

    @pytest.mark.asyncio
    async def test_export_html_success(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test exporting an article as HTML."""
        # Create article with HTML content
        html_content = """
        <h1>SEO Guide</h1>
        <p>This is a <strong>comprehensive</strong> guide.</p>
        <script>alert('bad')</script>
        <p onclick="evil()">Click me</p>
        """
        create_response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "SEO Guide",
                "workspace_id": str(test_workspace_id),
                "content": html_content,
            },
            headers=auth_headers,
        )
        article_id = create_response.json()["id"]

        # Export as HTML
        response = await async_client.get(
            f"/api/v1/articles/{article_id}/export?format=html",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == article_id
        assert data["title"] == "SEO Guide"
        assert data["format"] == "html"
        # Script tag should be removed
        assert "<script>" not in data["content"]
        assert "alert" not in data["content"]
        # onclick handler should be removed
        assert "onclick" not in data["content"]
        # Valid content should remain
        assert "<strong>comprehensive</strong>" in data["content"]

    @pytest.mark.asyncio
    async def test_export_markdown_success(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test exporting an article as Markdown."""
        # Create article with HTML content
        html_content = """
        <h1>Main Title</h1>
        <p>This is a <strong>bold</strong> and <em>italic</em> text.</p>
        <a href="https://example.com">Link</a>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        """
        create_response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "Main Title",
                "workspace_id": str(test_workspace_id),
                "content": html_content,
            },
            headers=auth_headers,
        )
        article_id = create_response.json()["id"]

        # Export as Markdown
        response = await async_client.get(
            f"/api/v1/articles/{article_id}/export?format=markdown",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == article_id
        assert data["format"] == "markdown"
        # Should have markdown formatting
        assert "# Main Title" in data["content"]
        assert "**bold**" in data["content"]
        assert "*italic*" in data["content"]
        assert "[Link](https://example.com)" in data["content"]
        assert "- Item 1" in data["content"]

    @pytest.mark.asyncio
    async def test_export_article_not_found(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test exporting non-existent article returns 404."""
        response = await async_client.get(
            f"/api/v1/articles/{uuid4()}/export?format=html",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_export_article_no_content(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test exporting article without content returns 400."""
        # Create article without content
        create_response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "Empty Article",
                "workspace_id": str(test_workspace_id),
            },
            headers=auth_headers,
        )
        article_id = create_response.json()["id"]

        # Try to export
        response = await async_client.get(
            f"/api/v1/articles/{article_id}/export?format=html",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "no content" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_export_invalid_format(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test exporting with invalid format returns 422."""
        create_response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "Test Article",
                "workspace_id": str(test_workspace_id),
                "content": "Some content",
            },
            headers=auth_headers,
        )
        article_id = create_response.json()["id"]

        response = await async_client.get(
            f"/api/v1/articles/{article_id}/export?format=pdf",
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_export_unauthorized(
        self,
        async_client: AsyncClient,
    ):
        """Test export without auth fails."""
        response = await async_client.get(
            f"/api/v1/articles/{uuid4()}/export?format=html",
        )
        assert response.status_code == 401


class TestPublishedPosts:
    """Tests for published posts tracking."""

    @pytest.mark.asyncio
    async def test_create_published_post_success(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
        db_session,
    ):
        """Test recording a manually published post."""
        # Create sites table for test
        await db_session.execute(
            text("""
                CREATE TABLE IF NOT EXISTS sites (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL
                )
            """)
        )
        site_id = uuid4()
        await db_session.execute(
            text("""
                INSERT INTO sites (id, workspace_id, name, domain)
                VALUES (:id, :workspace_id, :name, :domain)
            """),
            {
                "id": str(site_id),
                "workspace_id": str(test_workspace_id),
                "name": "Test Blog",
                "domain": "example.com",
            }
        )
        await db_session.commit()

        # Create article
        create_response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "Published Article",
                "workspace_id": str(test_workspace_id),
                "content": "Article content here",
            },
            headers=auth_headers,
        )
        article_id = create_response.json()["id"]

        # Record published post
        response = await async_client.post(
            "/api/v1/published-posts",
            json={
                "article_id": article_id,
                "site_id": str(site_id),
                "url": "https://example.com/blog/seo-guide",
                "wp_post_id": 123,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["article_id"] == article_id
        assert data["site_id"] == str(site_id)
        assert data["url"] == "https://example.com/blog/seo-guide"
        assert data["wp_post_id"] == 123
        assert data["status"] == "manual"
        assert data["published_at"] is not None

    @pytest.mark.asyncio
    async def test_create_published_post_article_not_found(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test creating published post with non-existent article returns 404."""
        response = await async_client.post(
            "/api/v1/published-posts",
            json={
                "article_id": str(uuid4()),
                "site_id": str(uuid4()),
            },
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "Article not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_published_post(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
        db_session,
    ):
        """Test getting a published post by ID."""
        # Create sites table for test
        await db_session.execute(
            text("""
                CREATE TABLE IF NOT EXISTS sites (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL
                )
            """)
        )
        site_id = uuid4()
        await db_session.execute(
            text("""
                INSERT INTO sites (id, workspace_id, name, domain)
                VALUES (:id, :workspace_id, :name, :domain)
            """),
            {
                "id": str(site_id),
                "workspace_id": str(test_workspace_id),
                "name": "Test Blog",
                "domain": "example.com",
            }
        )
        await db_session.commit()

        # Create article
        create_response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "Test Article",
                "workspace_id": str(test_workspace_id),
                "content": "Content",
            },
            headers=auth_headers,
        )
        article_id = create_response.json()["id"]

        # Create published post
        post_response = await async_client.post(
            "/api/v1/published-posts",
            json={
                "article_id": article_id,
                "site_id": str(site_id),
                "url": "https://example.com/post",
            },
            headers=auth_headers,
        )
        published_post_id = post_response.json()["id"]

        # Get published post
        response = await async_client.get(
            f"/api/v1/published-posts/{published_post_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == published_post_id
        assert data["article_id"] == article_id
        assert data["url"] == "https://example.com/post"

    @pytest.mark.asyncio
    async def test_get_published_post_not_found(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test getting non-existent published post returns 404."""
        response = await async_client.get(
            f"/api/v1/published-posts/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_published_posts_by_article(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
        db_session,
    ):
        """Test listing published posts for an article."""
        # Create sites table for test
        await db_session.execute(
            text("""
                CREATE TABLE IF NOT EXISTS sites (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL
                )
            """)
        )
        site_id = uuid4()
        await db_session.execute(
            text("""
                INSERT INTO sites (id, workspace_id, name, domain)
                VALUES (:id, :workspace_id, :name, :domain)
            """),
            {
                "id": str(site_id),
                "workspace_id": str(test_workspace_id),
                "name": "Test Blog",
                "domain": "example.com",
            }
        )
        await db_session.commit()

        # Create article
        create_response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "Article with Multiple Publications",
                "workspace_id": str(test_workspace_id),
                "content": "Content",
            },
            headers=auth_headers,
        )
        article_id = create_response.json()["id"]

        # Create multiple published posts
        for i in range(3):
            await async_client.post(
                "/api/v1/published-posts",
                json={
                    "article_id": article_id,
                    "site_id": str(site_id),
                    "url": f"https://example.com/post-{i}",
                },
                headers=auth_headers,
            )

        # List published posts
        response = await async_client.get(
            f"/api/v1/articles/{article_id}/published-posts",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_create_published_post_unauthorized(
        self,
        async_client: AsyncClient,
    ):
        """Test creating published post without auth fails."""
        response = await async_client.post(
            "/api/v1/published-posts",
            json={
                "article_id": str(uuid4()),
                "site_id": str(uuid4()),
            },
        )
        assert response.status_code == 401


class TestPublishingService:
    """Tests for publishing service utilities."""

    def test_clean_html_removes_scripts(self):
        """Test that clean_html_for_wordpress removes script tags."""
        from app.services.publishing_service import clean_html_for_wordpress

        html = """
        <p>Safe content</p>
        <script>alert('xss')</script>
        <p>More content</p>
        """
        result = clean_html_for_wordpress(html)
        assert "<script>" not in result
        assert "alert" not in result
        assert "Safe content" in result
        assert "More content" in result

    def test_clean_html_removes_event_handlers(self):
        """Test that clean_html_for_wordpress removes on* event handlers."""
        from app.services.publishing_service import clean_html_for_wordpress

        html = '<p onclick="evil()">Click me</p><a onmouseover="bad()">Link</a>'
        result = clean_html_for_wordpress(html)
        assert "onclick" not in result
        assert "onmouseover" not in result
        assert "Click me" in result

    def test_clean_html_removes_javascript_urls(self):
        """Test that clean_html_for_wordpress removes javascript: URLs."""
        from app.services.publishing_service import clean_html_for_wordpress

        html = '<a href="javascript:alert(1)">Bad link</a>'
        result = clean_html_for_wordpress(html)
        assert "javascript:" not in result

    def test_clean_html_removes_iframes(self):
        """Test that clean_html_for_wordpress removes iframe tags."""
        from app.services.publishing_service import clean_html_for_wordpress

        html = '<p>Content</p><iframe src="https://evil.com"></iframe><p>More</p>'
        result = clean_html_for_wordpress(html)
        assert "<iframe" not in result
        assert "Content" in result

    def test_convert_html_to_markdown_headers(self):
        """Test markdown conversion of headers."""
        from app.services.publishing_service import convert_html_to_markdown

        html = "<h1>Title</h1><h2>Subtitle</h2><h3>Section</h3>"
        result = convert_html_to_markdown(html)
        assert "# Title" in result
        assert "## Subtitle" in result
        assert "### Section" in result

    def test_convert_html_to_markdown_formatting(self):
        """Test markdown conversion of text formatting."""
        from app.services.publishing_service import convert_html_to_markdown

        html = "<strong>bold</strong> and <em>italic</em>"
        result = convert_html_to_markdown(html)
        assert "**bold**" in result
        assert "*italic*" in result

    def test_convert_html_to_markdown_links(self):
        """Test markdown conversion of links."""
        from app.services.publishing_service import convert_html_to_markdown

        html = '<a href="https://example.com">Example</a>'
        result = convert_html_to_markdown(html)
        assert "[Example](https://example.com)" in result

    def test_convert_html_to_markdown_lists(self):
        """Test markdown conversion of lists."""
        from app.services.publishing_service import convert_html_to_markdown

        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"
        result = convert_html_to_markdown(html)
        assert "- Item 1" in result
        assert "- Item 2" in result

    def test_convert_html_to_markdown_empty_content(self):
        """Test markdown conversion handles empty content."""
        from app.services.publishing_service import convert_html_to_markdown

        assert convert_html_to_markdown("") == ""
        assert convert_html_to_markdown(None) == ""

    def test_clean_html_empty_content(self):
        """Test clean_html handles empty content."""
        from app.services.publishing_service import clean_html_for_wordpress

        assert clean_html_for_wordpress("") == ""
        assert clean_html_for_wordpress(None) == ""
