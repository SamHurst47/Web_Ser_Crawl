"""
test_crawler.py - Unit tests for web crawler functionality.

Tests the QuoteCrawler class with mocked HTTP requests to verify
crawling logic, pagination handling, and error recovery.

Run with: 
    pytest tests/test_crawler.py -v          # Skip live tests
    pytest tests/test_crawler.py -v -m live  # Include live tests
"""

import os
import sys
import pytest
import requests
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crawler import QuoteCrawler


# === Mock HTML Responses ===

MOCK_HTML = """
<html>
    <body>
        <div class="quote">
            <span class="text">"Test quote one."</span>
            <small class="author">Author A</small>
        </div>
        <div class="quote">
            <span class="text">"Test quote two."</span>
            <small class="author">Author B</small>
        </div>
    </body>
</html>
"""

MOCK_HTML_WITH_PAGINATION = """
<html>
    <body>
        <div class="quote">
            <span class="text">"First page quote."</span>
            <small class="author">Author X</small>
        </div>
        <li class="next">
            <a href="/page/2/">Next →</a>
        </li>
    </body>
</html>
"""

MOCK_HTML_PAGE_2 = """
<html>
    <body>
        <div class="quote">
            <span class="text">"Second page quote."</span>
            <small class="author">Author Y</small>
        </div>
    </body>
</html>
"""


class DummyResponse:
    """Mock HTTP response object for testing."""
    
    def __init__(self, text, status_code=200):
        """
        Initialize mock response.
        
        Args:
            text (str): HTML content
            status_code (int): HTTP status code
        """
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        """Raise exception for non-200 status codes."""
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")


class TestQuoteCrawler:
    """Test suite for QuoteCrawler with mocked requests."""
    
    @patch('src.crawler.requests.get')
    @patch('src.crawler.time.sleep')  # Mock sleep to speed up tests
    def test_crawl_success(self, mock_sleep, mock_get):
        """Test successful crawl with valid HTML."""
        mock_get.return_value = DummyResponse(MOCK_HTML)

        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        # Verify correct number of results
        assert len(results) == 2
        
        # Verify first quote
        assert results[0]['author'] == "Author A"
        assert results[0]['text'] == '"Test quote one."'
        
        # Verify second quote
        assert results[1]['author'] == "Author B"
        assert results[1]['text'] == '"Test quote two."'

    @patch('src.crawler.requests.get')
    def test_crawl_network_error(self, mock_get):
        """Test handling of network exceptions."""
        mock_get.side_effect = requests.exceptions.RequestException("Network down")
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        # Should return empty list on network error
        assert results == []

    @patch('src.crawler.requests.get')
    def test_crawl_timeout(self, mock_get):
        """Test crawler handles timeouts gracefully."""
        mock_get.side_effect = requests.exceptions.Timeout("Server timed out")
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        # Should return empty list on timeout
        assert results == []

    @patch('src.crawler.requests.get')
    def test_crawl_malformed_html(self, mock_get):
        """Test handling of HTML without expected quote structure."""
        malformed_html = "<html><body><h1>Site Under Construction</h1></body></html>"
        mock_get.return_value = DummyResponse(malformed_html)

        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        # Should return empty list when no quotes found
        assert results == []
        
    @patch('src.crawler.requests.get')
    def test_crawl_404_not_found(self, mock_get):
        """Test HTTP 404 error handling."""
        mock_get.return_value = DummyResponse("Not Found", status_code=404)
        
        crawler = QuoteCrawler("http://fakeurl.com/does-not-exist")
        results = crawler.crawl()
        
        # Should return empty list on 404
        assert results == []

    @patch('src.crawler.requests.get')
    def test_crawl_500_server_error(self, mock_get):
        """Test handling of server errors (5xx)."""
        mock_get.return_value = DummyResponse(
            "Internal Server Error",
            status_code=500
        )
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        # Should return empty list on server error
        assert results == []

    @patch('src.crawler.requests.get')
    @patch('src.crawler.time.sleep')
    def test_crawl_pagination(self, mock_sleep, mock_get):
        """Test that crawler follows pagination links."""
        # Mock returns different pages in sequence
        mock_get.side_effect = [
            DummyResponse(MOCK_HTML_WITH_PAGINATION),
            DummyResponse(MOCK_HTML_PAGE_2)
        ]
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        # Should have crawled both pages
        assert len(results) == 2
        assert results[0]['text'] == '"First page quote."'
        assert results[1]['text'] == '"Second page quote."'
        
        # Should have made 2 requests
        assert mock_get.call_count == 2

    @patch('src.crawler.requests.get')
    def test_crawl_connection_error(self, mock_get):
        """Test handling of connection failures."""
        mock_get.side_effect = requests.exceptions.ConnectionError(
            "Failed to connect"
        )
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        # Should return empty list on connection error
        assert results == []

    @patch('src.crawler.requests.get')
    def test_crawl_empty_quotes(self, mock_get):
        """Test handling of malformed quote blocks."""
        # HTML with one valid quote and two malformed quotes
        html_missing_fields = """
        <html><body>
            <div class="quote">
                <span class="text">"Valid quote"</span>
                <small class="author">Valid Author</small>
            </div>
            <div class="quote">
                <span class="text">"Missing author"</span>
            </div>
            <div class="quote">
                <small class="author">Missing quote text</small>
            </div>
        </body></html>
        """
        mock_get.return_value = DummyResponse(html_missing_fields)
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        # Should only get the one valid quote
        assert len(results) == 1
        assert results[0]['text'] == '"Valid quote"'
        assert results[0]['author'] == 'Valid Author'

    def test_page_number_extraction(self):
        """Test _get_page_number helper method."""
        crawler = QuoteCrawler()
        
        # Base URL should be page 1
        assert crawler._get_page_number("https://quotes.toscrape.com/") == 1
        
        # Page URLs should extract number correctly
        assert crawler._get_page_number("https://quotes.toscrape.com/page/2/") == 2
        assert crawler._get_page_number("https://quotes.toscrape.com/page/10/") == 10
        assert crawler._get_page_number("https://quotes.toscrape.com/page/100/") == 100


@pytest.mark.live
class TestQuoteCrawlerLive:
    """Live tests that require internet connection."""
    
    def test_crawl_real_site(self):
        """Test crawling the actual quotes.toscrape.com site."""
        crawler = QuoteCrawler("https://quotes.toscrape.com")
        results = crawler.crawl()
        
        # The real site should have quotes
        assert len(results) > 0, "Live site should return quotes"
        
        # Verify structure of first result
        assert 'page_number' in results[0]
        assert 'url' in results[0]
        assert 'author' in results[0]
        assert 'text' in results[0]
        
        # Verify data types
        assert isinstance(results[0]['author'], str)
        assert isinstance(results[0]['text'], str)
        assert len(results[0]['author']) > 0
        assert len(results[0]['text']) > 0
        
        # First page should be page 1
        assert results[0]['page_number'] == 1
        
        # Should crawl multiple pages
        page_numbers = set(r['page_number'] for r in results)
        assert len(page_numbers) > 1, "Should crawl multiple pages"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])