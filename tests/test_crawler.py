import os
import sys
import pytest
import requests
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crawler import QuoteCrawler


# --- Dummy Data ---
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
    """Mock response object that mimics requests.Response"""
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")


class TestQuoteCrawler:
    """Test suite for QuoteCrawler with mocked requests"""
    
    @patch('src.crawler.requests.get')
    @patch('src.crawler.time.sleep')  # Mock sleep to speed up tests
    def test_crawl_success(self, mock_sleep, mock_get):
        """Test the happy path where the site responds perfectly"""
        mock_get.return_value = DummyResponse(MOCK_HTML)

        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        # Verify we got results
        assert len(results) == 2, f"Expected 2 results, got {len(results)}"
        assert results[0]['author'] == "Author A"
        assert results[0]['text'] == '"Test quote one."'
        assert results[1]['author'] == "Author B"
        assert results[1]['text'] == '"Test quote two."'

    @patch('src.crawler.requests.get')
    def test_crawl_network_error(self, mock_get):
        """Test handling of standard network exceptions"""
        mock_get.side_effect = requests.exceptions.RequestException("Network down")
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        assert results == []

    @patch('src.crawler.requests.get')
    def test_crawl_timeout(self, mock_get):
        """Test crawler handles timeouts gracefully"""
        mock_get.side_effect = requests.exceptions.Timeout("Server timed out")
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        assert results == []

    @patch('src.crawler.requests.get')
    def test_crawl_malformed_html(self, mock_get):
        """Test handling of HTML without expected quote structure"""
        mock_get.return_value = DummyResponse("<html><body><h1>Site Under Construction</h1></body></html>")

        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        assert results == []
        
    @patch('src.crawler.requests.get')
    def test_crawl_404_not_found(self, mock_get):
        """Test HTTP error codes like 404"""
        mock_get.return_value = DummyResponse("Not Found", status_code=404)
        
        crawler = QuoteCrawler("http://fakeurl.com/does-not-exist")
        results = crawler.crawl()
        
        assert results == []

    @patch('src.crawler.requests.get')
    def test_crawl_500_server_error(self, mock_get):
        """Test handling of server errors"""
        mock_get.return_value = DummyResponse("Internal Server Error", status_code=500)
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        assert results == []

    @patch('src.crawler.requests.get')
    @patch('src.crawler.time.sleep')
    def test_crawl_pagination(self, mock_sleep, mock_get):
        """Test that crawler follows pagination links"""
        # Set up mock to return different pages
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
        assert mock_get.call_count == 2

    @patch('src.crawler.requests.get')
    def test_crawl_connection_error(self, mock_get):
        """Test handling of connection failures"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        assert results == []

    @patch('src.crawler.requests.get')
    def test_crawl_empty_quotes(self, mock_get):
        """Test handling of page with quote divs but missing required fields"""
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


@pytest.mark.live
class TestQuoteCrawlerLive:
    """Live tests that require internet connection"""
    
    def test_crawl_real_site(self):
        """Test crawling the actual quotes.toscrape.com site"""
        crawler = QuoteCrawler("https://quotes.toscrape.com")
        results = crawler.crawl()
        
        # The real site should have quotes
        assert len(results) > 0, "Live site should return quotes"
        
        # Verify structure
        assert 'author' in results[0]
        assert 'text' in results[0]
        assert isinstance(results[0]['author'], str)
        assert isinstance(results[0]['text'], str)
        assert len(results[0]['author']) > 0
        assert len(results[0]['text']) > 0