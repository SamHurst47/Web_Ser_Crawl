import requests
from bs4 import BeautifulSoup
import time

class QuoteCrawler:
    def __init__(self, base_url="https://quotes.toscrape.com"):
        self.base_url = base_url

    def crawl(self):
        """Navigates the site, extracts quote data, and enforces politeness."""
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

                for q in quotes:
                    found_quotes.append({
                        'author': q.find('small', class_='author').get_text(strip=True),
                        'text': q.find('span', class_='text').get_text(strip=True)
                    })

                next_btn = soup.find('li', class_='next')
                if next_btn and next_btn.find('a'):
                    current_url = f"https://quotes.toscrape.com{next_btn.find('a')['href']}"
                else:
                    current_url = None 
                    
                # MANDATORY POLITENESS WINDOW
                if current_url:
                    print("    -> Sleeping for 6 seconds to respect server politeness window...")
                    time.sleep(6)
                    
            # --- THE PROTECTIVE SHIELD IS BACK ---
            except requests.exceptions.RequestException as e:
                print(f"[-] Network error encountered: {e}")
                break
            except Exception as e:
                print(f"[-] Unexpected error during parsing: {e}")
                break
            
        return found_quotes