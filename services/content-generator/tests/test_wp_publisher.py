"""Tests for WordPress Publisher and Publishing Automation."""

from uuid import uuid4

import pytest

from app.models.article import Article
from app.services.wp_publisher import WordPressPublisher, Site
from app.services.google_indexer import GoogleIndexer


class TestWordPressPublisher:
    """Tests for WordPress Publisher service."""

    @pytest.mark.asyncio
    async def test_publish_article_mock_mode(self):
        """Test publishing an article in mock mode."""
        publisher = WordPressPublisher(mock_mode=True)
        
        article = Article()
        article.id = uuid4()
        article.title = "Test SEO Article"
        article.content = "<h1>Test Content</h1><p>This is test content.</p>"
        
        site = Site(
            id=uuid4(),
            wp_api_endpoint="https://example.com",
            wp_username="testuser",
            wp_app_password="test-app-password",
        )
        
        result = await publisher.publish(article, site)
        
        assert result["status"] == "published"
        assert result["wp_post_id"] == 12345
        assert "mock-post" in result["url"]
        
        # Verify mock response was recorded
        assert len(publisher.mock_responses) == 1
        assert publisher.mock_responses[0]["article_id"] == str(article.id)

    @pytest.mark.asyncio
    async def test_publish_article_with_categories(self):
        """Test publishing an article with categories and tags."""
        publisher = WordPressPublisher(mock_mode=True)
        
        article = Article()
        article.id = uuid4()
        article.title = "SEO Guide"
        article.content = "<p>Complete SEO guide content.</p>"
        
        site = Site(
            id=uuid4(),
            wp_api_endpoint="https://blog.example.com",
            wp_username="admin",
            wp_app_password="secret",
        )
        
        result = await publisher.publish(
            article, 
            site,
            categories=[1, 2],
            tags=[5, 6],
        )
        
        assert result["status"] == "published"
        # Verify categories were in payload
        mock_response = publisher.mock_responses[0]
        assert mock_response["payload"]["categories"] == [1, 2]
        assert mock_response["payload"]["tags"] == [5, 6]

    @pytest.mark.asyncio
    async def test_update_post_mock_mode(self):
        """Test updating a WordPress post in mock mode."""
        publisher = WordPressPublisher(mock_mode=True)
        
        site = Site(
            id=uuid4(),
            wp_api_endpoint="https://example.com",
            wp_username="testuser",
            wp_app_password="test",
        )
        
        result = await publisher.update_post(
            wp_post_id=12345,
            site=site,
            title="Updated Title",
            content="<p>Updated content</p>",
        )
        
        assert result["id"] == 12345
        assert result["title"]["rendered"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_delete_post_mock_mode(self):
        """Test deleting a WordPress post in mock mode."""
        publisher = WordPressPublisher(mock_mode=True)
        
        site = Site(
            id=uuid4(),
            wp_api_endpoint="https://example.com",
            wp_username="testuser",
            wp_app_password="test",
        )
        
        result = await publisher.delete_post(wp_post_id=12345, site=site)
        
        assert result["deleted"] is True
        assert result["id"] == 12345

    @pytest.mark.asyncio
    async def test_get_categories_mock_mode(self):
        """Test getting WordPress categories in mock mode."""
        publisher = WordPressPublisher(mock_mode=True)
        
        site = Site(
            id=uuid4(),
            wp_api_endpoint="https://example.com",
            wp_username="testuser",
            wp_app_password="test",
        )
        
        categories = await publisher.get_categories(site)
        
        assert len(categories) == 2
        assert categories[0]["name"] == "Uncategorized"
        assert categories[1]["slug"] == "seo"

    @pytest.mark.asyncio
    async def test_get_tags_mock_mode(self):
        """Test getting WordPress tags in mock mode."""
        publisher = WordPressPublisher(mock_mode=True)
        
        site = Site(
            id=uuid4(),
            wp_api_endpoint="https://example.com",
            wp_username="testuser",
            wp_app_password="test",
        )
        
        tags = await publisher.get_tags(site)
        
        assert len(tags) == 2
        assert tags[0]["name"] == "seo"

    def test_clear_mock_responses(self):
        """Test clearing mock responses."""
        publisher = WordPressPublisher(mock_mode=True)
        publisher._mock_responses = [{"test": "data"}]
        
        publisher.clear_mock_responses()
        
        assert len(publisher.mock_responses) == 0


class TestGoogleIndexer:
    """Tests for Google Indexing API service."""

    @pytest.mark.asyncio
    async def test_request_indexing_mock_mode(self):
        """Test requesting indexing in mock mode."""
        indexer = GoogleIndexer(mock_mode=True)
        
        result = await indexer.request_indexing("https://example.com/new-post")
        
        assert "urlNotificationMetadata" in result
        assert result["urlNotificationMetadata"]["url"] == "https://example.com/new-post"
        
        # Verify mock request was recorded
        assert len(indexer.mock_requests) == 1
        assert indexer.mock_requests[0]["type"] == "URL_UPDATED"

    @pytest.mark.asyncio
    async def test_request_removal_mock_mode(self):
        """Test requesting removal in mock mode."""
        indexer = GoogleIndexer(mock_mode=True)
        
        result = await indexer.request_removal("https://example.com/old-post")
        
        assert "urlNotificationMetadata" in result
        assert indexer.mock_requests[0]["type"] == "URL_DELETED"

    @pytest.mark.asyncio
    async def test_get_notification_status_mock_mode(self):
        """Test getting notification status in mock mode."""
        indexer = GoogleIndexer(mock_mode=True)
        
        result = await indexer.get_notification_status("https://example.com/post")
        
        assert result["url"] == "https://example.com/post"
        assert "latestUpdate" in result

    @pytest.mark.asyncio
    async def test_batch_request_indexing(self):
        """Test batch requesting indexing."""
        indexer = GoogleIndexer(mock_mode=True)
        
        urls = [
            "https://example.com/post-1",
            "https://example.com/post-2",
            "https://example.com/post-3",
        ]
        
        results = await indexer.batch_request_indexing(urls)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["url"] == urls[i]
            assert "result" in result

    def test_clear_mock_requests(self):
        """Test clearing mock requests."""
        indexer = GoogleIndexer(mock_mode=True)
        indexer._mock_requests = [{"test": "data"}]
        
        indexer.clear_mock_requests()
        
        assert len(indexer.mock_requests) == 0

    def test_no_credentials_error(self):
        """Test error when no credentials provided."""
        indexer = GoogleIndexer(mock_mode=False)
        
        # Without credentials, get_service should return None
        service = indexer._get_service()
        assert service is None


class TestWordPressPublisherWithGoogleIndexer:
    """Tests for WordPress Publisher with Google Indexer integration."""

    @pytest.mark.asyncio
    async def test_publish_with_google_indexing(self):
        """Test publishing triggers Google indexing."""
        google_indexer = GoogleIndexer(mock_mode=True)
        publisher = WordPressPublisher(
            mock_mode=True,
            google_indexer=google_indexer,
        )
        
        article = Article()
        article.id = uuid4()
        article.title = "New Article"
        article.content = "<p>Content for indexing</p>"
        
        site = Site(
            id=uuid4(),
            wp_api_endpoint="https://example.com",
            wp_username="user",
            wp_app_password="pass",
        )
        
        await publisher.publish(article, site)
        
        # Verify Google indexing was requested
        assert len(google_indexer.mock_requests) == 1
        assert "mock-post" in google_indexer.mock_requests[0]["url"]
