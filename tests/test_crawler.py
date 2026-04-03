import pytest
import requests
from unittest.mock import patch, MagicMock
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

# A dummy class guarantees BeautifulSoup treats this exactly like a real requests response
class DummyResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    # Mimics the requests library's error checking
    def raise_for_status(self):
        if self.status_code != 200:
            import requests
            raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")
class TestQuoteCrawler:
    @patch('src.crawler.requests.get')
    def test_crawl_success(self, mock_get):
        """Test the 'happy path' where the site responds perfectly."""
        # Use our dummy class instead of MagicMock
        mock_get.return_value = DummyResponse(MOCK_HTML)

        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        # If the try/except block in crawler.py caught an error, results will be empty. 
        # This will forcefully fail the test and tell us what to do.
        if len(results) == 0:
            pytest.fail("Crawler returned an empty list! A hidden exception was caught in crawler.py. Run 'pytest -s' to see the crawler's error print statement.")

        assert len(results) == 2
        assert results[0]['author'] == "Author A"
        assert results[1]['text'] == '"Test quote two."'

    @patch('src.crawler.requests.get')
    def test_crawl_network_error(self, mock_get):
        """Test handling of standard network exceptions."""
        mock_get.side_effect = requests.exceptions.RequestException("Network down")
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        assert results == []

    @patch('src.crawler.requests.get')
    def test_crawl_timeout(self, mock_get):
        """Test how the crawler handles a server that takes too long to respond."""
        mock_get.side_effect = requests.exceptions.Timeout("Server timed out")
        
        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        assert results == []

    @patch('src.crawler.requests.get')
    def test_crawl_malformed_html(self, mock_get):
        """Test what happens if the site's HTML changes and the expected tags are missing."""
        mock_get.return_value = DummyResponse("<html><body><h1>Site Under Construction</h1></body></html>")

        crawler = QuoteCrawler("http://fakeurl.com")
        results = crawler.crawl()
        
        assert results == []
        
    @patch('src.crawler.requests.get')
    def test_crawl_404_not_found(self, mock_get):
        """Test HTTP error codes like 404 or 500."""
        mock_get.return_value = DummyResponse("Not Found", status_code=404)
        
        crawler = QuoteCrawler("http://fakeurl.com/does-not-exist")
        results = crawler.crawl()
        
        assert results == []