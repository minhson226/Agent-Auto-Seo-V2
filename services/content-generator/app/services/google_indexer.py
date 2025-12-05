"""Google Indexing API service for requesting URL indexing."""

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GoogleIndexer:
    """Service for interacting with Google Indexing API.

    This service sends URL update/delete notifications to Google to
    request indexing of published content.
    """

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[Dict[str, Any]] = None,
        mock_mode: bool = False,
    ):
        """Initialize the Google Indexer.

        Args:
            credentials_path: Path to service account JSON file
            credentials_json: Service account credentials as dict
            mock_mode: If True, simulate API calls without real requests
        """
        self._credentials_path = credentials_path
        self._credentials_json = credentials_json
        self._mock_mode = mock_mode
        self._mock_requests: List[Dict[str, Any]] = []
        self._service = None

    @property
    def mock_mode(self) -> bool:
        """Check if indexer is in mock mode."""
        return self._mock_mode

    @property
    def mock_requests(self) -> List[Dict[str, Any]]:
        """Get list of mock requests (for testing)."""
        return self._mock_requests

    def clear_mock_requests(self) -> None:
        """Clear mock requests (for testing)."""
        self._mock_requests = []

    def _get_service(self):
        """Get or create the Google Indexing API service."""
        if self._service is not None:
            return self._service

        if self._mock_mode:
            return None

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            if self._credentials_json:
                credentials = service_account.Credentials.from_service_account_info(
                    self._credentials_json,
                    scopes=["https://www.googleapis.com/auth/indexing"],
                )
            elif self._credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    self._credentials_path,
                    scopes=["https://www.googleapis.com/auth/indexing"],
                )
            else:
                raise ValueError(
                    "Either credentials_path or credentials_json must be provided"
                )

            self._service = build("indexing", "v3", credentials=credentials)
            return self._service
        except ImportError:
            logger.warning(
                "Google API libraries not installed. "
                "Install google-auth and google-api-python-client."
            )
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Google Indexing service: {e}")
            return None

    async def request_indexing(self, url: str) -> Dict[str, Any]:
        """Request Google to index a URL.

        Args:
            url: The URL to request indexing for

        Returns:
            Dict with API response or mock response
        """
        if self._mock_mode:
            mock_response = {
                "urlNotificationMetadata": {
                    "url": url,
                    "latestUpdate": {
                        "type": "URL_UPDATED",
                        "notifyTime": "2024-01-01T00:00:00Z",
                    },
                }
            }
            self._mock_requests.append({
                "url": url,
                "type": "URL_UPDATED",
                "response": mock_response,
            })
            logger.info(f"Mock requested indexing for: {url}")
            return mock_response

        service = self._get_service()
        if not service:
            logger.warning(f"Google Indexing service not available for URL: {url}")
            return {"error": "Service not available"}

        try:
            body = {
                "url": url,
                "type": "URL_UPDATED",
            }
            response = service.urlNotifications().publish(body=body).execute()
            logger.info(f"Requested Google indexing for: {url}")
            return response
        except Exception as e:
            logger.error(f"Failed to request indexing for {url}: {e}")
            return {"error": str(e)}

    async def request_removal(self, url: str) -> Dict[str, Any]:
        """Request Google to remove a URL from index.

        Args:
            url: The URL to request removal for

        Returns:
            Dict with API response or mock response
        """
        if self._mock_mode:
            mock_response = {
                "urlNotificationMetadata": {
                    "url": url,
                    "latestUpdate": {
                        "type": "URL_DELETED",
                        "notifyTime": "2024-01-01T00:00:00Z",
                    },
                }
            }
            self._mock_requests.append({
                "url": url,
                "type": "URL_DELETED",
                "response": mock_response,
            })
            logger.info(f"Mock requested removal for: {url}")
            return mock_response

        service = self._get_service()
        if not service:
            logger.warning(f"Google Indexing service not available for URL: {url}")
            return {"error": "Service not available"}

        try:
            body = {
                "url": url,
                "type": "URL_DELETED",
            }
            response = service.urlNotifications().publish(body=body).execute()
            logger.info(f"Requested Google removal for: {url}")
            return response
        except Exception as e:
            logger.error(f"Failed to request removal for {url}: {e}")
            return {"error": str(e)}

    async def get_notification_status(self, url: str) -> Dict[str, Any]:
        """Get the indexing notification status for a URL.

        Args:
            url: The URL to check status for

        Returns:
            Dict with status information
        """
        if self._mock_mode:
            return {
                "url": url,
                "latestUpdate": {
                    "type": "URL_UPDATED",
                    "notifyTime": "2024-01-01T00:00:00Z",
                },
            }

        service = self._get_service()
        if not service:
            return {"error": "Service not available"}

        try:
            response = service.urlNotifications().getMetadata(url=url).execute()
            return response
        except Exception as e:
            logger.error(f"Failed to get status for {url}: {e}")
            return {"error": str(e)}

    async def batch_request_indexing(
        self,
        urls: List[str],
    ) -> List[Dict[str, Any]]:
        """Request indexing for multiple URLs.

        Args:
            urls: List of URLs to request indexing for

        Returns:
            List of responses for each URL
        """
        results = []
        for url in urls:
            result = await self.request_indexing(url)
            results.append({"url": url, "result": result})
        return results
