"""
crawler.py - Web crawler for extracting quotes from quotes.toscrape.com.

Implements a polite web crawler that extracts quotes, author information,
and page numbers. Follows pagination links and respects server politeness
with a 6-second delay between requests.

Example:
    >>> from crawler import QuoteCrawler
    >>> crawler = QuoteCrawler()
    >>> quotes = crawler.crawl()
    >>> for quote in quotes:
    ...     print(f"Page {quote['page_number']}: {quote['text']}")
"""

import re
import time
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup


class QuoteCrawler:
    """
    Web crawler for extracting quotes from quotes.toscrape.com.
    
    Navigates through paginated quote collections, extracting quote text,
    author names, and maintaining page number associations. Implements
    politeness delays and robust error handling.
    
    Attributes:
        base_url (str): The starting URL for the crawl
    
    Example:
        >>> crawler = QuoteCrawler("https://quotes.toscrape.com")
        >>> results = crawler.crawl()
        >>> len(results) > 0
        True
    """
    
    POLITENESS_DELAY_SECONDS: int = 6
    REQUEST_TIMEOUT_SECONDS: int = 10
    
    def __init__(self, base_url: str = "https://quotes.toscrape.com") -> None:
        """
        Initialize the QuoteCrawler with a base URL.
        
        Args:
            base_url (str, optional): Starting URL for crawling.
                Defaults to "https://quotes.toscrape.com".
        """
        self.base_url: str = base_url

    def _get_page_number(self, url: str) -> int:
        """
        Extract page number from a URL.
        
        Args:
            url (str): The URL to parse
        
        Returns:
            int: Page number from URL, or 1 for base page
        
        Examples:
            >>> crawler = QuoteCrawler()
            >>> crawler._get_page_number("https://quotes.toscrape.com/page/2/")
            2
        """
        match = re.search(r'/page/(\d+)/', url)
        if match:
            return int(match.group(1))
        return 1

    def crawl(self) -> List[Dict[str, any]]:
        """
        Navigate the site and extract all quote data with page associations.
        
        Performs the main crawling operation:
        1. Fetches each page starting from base_url
        2. Extracts quote text and author from each page
        3. Associates quotes with source page number
        4. Follows pagination links
        5. Enforces politeness delay between requests
        
        Returns:
            List[Dict[str, any]]: List of dictionaries containing:
                - 'page_number' (int): Page number where quote was found
                - 'url' (str): URL of the page
                - 'author' (str): Quote author name
                - 'text' (str): Quote text
                Returns empty list if crawling fails.
        
        Note:
            Implements 6-second politeness delay between requests.
            Handles network errors gracefully without raising exceptions.
        """
        found_quotes: List[Dict[str, any]] = []
        current_url: Optional[str] = self.base_url
        
        while current_url:
            print(f"[*] Fetching: {current_url}")
            
            try:
                # Fetch page with timeout
                response = requests.get(
                    current_url,
                    timeout=self.REQUEST_TIMEOUT_SECONDS
                )
                
                # Check for HTTP errors
                if response.status_code != 200:
                    print(f"[-] Stopped: Received status code {response.status_code}")
                    break
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                quotes = soup.find_all('div', class_='quote')

                if not quotes:
                    print("[-] No quotes found on this page. Stopping crawl.")
                    break

                # Extract page number from URL
                page_number: int = self._get_page_number(current_url)

                # Process each quote block
                for quote_block in quotes:
                    try:
                        author_elem = quote_block.find('small', class_='author')
                        text_elem = quote_block.find('span', class_='text')

                        # Skip malformed quote blocks
                        if not author_elem or not text_elem:
                            print("    [!] Skipping malformed quote block.")
                            continue

                        found_quotes.append({
                            'page_number': page_number,
                            'url': current_url,
                            'author': author_elem.get_text(strip=True),
                            'text': text_elem.get_text(strip=True)
                        })
                        
                    except Exception as e:
                        print(f"    [!] Could not parse one quote block: {e}")
                        continue

                # Look for pagination "next" button
                next_btn = soup.find('li', class_='next')
                if next_btn and next_btn.find('a'):
                    next_href: str = next_btn.find('a')['href']
                    current_url = f"https://quotes.toscrape.com{next_href}"
                else:
                    current_url = None
                    
                # Enforce politeness delay
                if current_url:
                    print(
                        f"    -> Sleeping for {self.POLITENESS_DELAY_SECONDS} "
                        "seconds to respect server politeness window..."
                    )
                    time.sleep(self.POLITENESS_DELAY_SECONDS)
                    
            except requests.exceptions.ConnectionError as e:
                print(f"[-] Connection error encountered: {e}")
                break
            except requests.exceptions.Timeout:
                print(f"[-] Request timed out for: {current_url}")
                break
            except requests.exceptions.RequestException as e:
                print(f"[-] Network error encountered: {e}")
                break
            except Exception as e:
                print(f"[-] Unexpected error during parsing: {e}")
                break
        
        return found_quotes