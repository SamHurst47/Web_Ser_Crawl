import requests
from bs4 import BeautifulSoup
import time
import re

class QuoteCrawler:
    def __init__(self, base_url="https://quotes.toscrape.com"):
        self.base_url = base_url

    def _get_page_number(self, url):
        """Extract page number from URL. Returns 1 for base page."""
        match = re.search(r'/page/(\d+)/', url)
        if match:
            return int(match.group(1))
        return 1  # Base URL is page 1

    def crawl(self):
        """Navigates the site, extracts quote data with page numbers, and enforces politeness."""
        found_quotes = []
        current_url = self.base_url
        
        while current_url:
            print(f"[*] Fetching: {current_url}")
            try:
                # 10-second timeout to prevent hanging
                response = requests.get(current_url, timeout=10)
                
                # Check for 404/500 errors
                if response.status_code != 200:
                    print(f"[-] Stopped: Received status code {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                quotes = soup.find_all('div', class_='quote')

                if not quotes:
                    print("[-] No quotes found on this page. Stopping crawl.")
                    break

                # Get page number from URL
                page_number = self._get_page_number(current_url)

                for q in quotes:
                    try:
                        author = q.find('small', class_='author')
                        text = q.find('span', class_='text')

                        # Skip malformed quote blocks
                        if not author or not text:
                            print("    [!] Skipping malformed quote block.")
                            continue

                        found_quotes.append({
                            'page_number': page_number,  # Use actual page number
                            'url': current_url,
                            'author': author.get_text(strip=True),
                            'text': text.get_text(strip=True)
                        })
                    except Exception as e:
                        print(f"    [!] Could not parse one quote block: {e}")
                        continue

                next_btn = soup.find('li', class_='next')
                if next_btn and next_btn.find('a'):
                    current_url = f"https://quotes.toscrape.com{next_btn.find('a')['href']}"
                else:
                    current_url = None 
                    
                # MANDATORY POLITENESS WINDOW
                if current_url:
                    print("    -> Sleeping for 6 seconds to respect server politeness window...")
                    time.sleep(6)
                    
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