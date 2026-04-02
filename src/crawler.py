import requests
from bs4 import BeautifulSoup

class QuoteCrawler:
    def __init__(self, base_url="https://quotes.toscrape.com"):
        self.base_url = base_url

    def crawl(self):
        found_quotes = []
        current_url = self.base_url
        
        while current_url:
            try:
                response = requests.get(current_url, timeout=10)
                if response.status_code != 200: break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                for q in soup.find_all('div', class_='quote'):
                    found_quotes.append({
                        'author': q.find('small', class_='author').get_text(),
                        'text': q.find('span', class_='text').get_text()
                    })

                next_btn = soup.find('li', class_='next')
                current_url = f"https://quotes.toscrape.com{next_btn.find('a')['href']}" if next_btn else None
            except Exception:
                break
            
        return found_quotes