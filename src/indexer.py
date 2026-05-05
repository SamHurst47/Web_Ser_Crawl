import os
import re
import json
import math
from collections import defaultdict

class IndexManager:
    def __init__(self):
        # Points to ../data/inverted_index.json
        self.data_dir = os.path.join(os.getcwd(), "..", "data")
        self.index_path = os.path.join(self.data_dir, "inverted_index.json")
        self.inverted_index = {}
        self.tf_idf_scores = {}
        self.page_urls = {}  # Maps page_id to URL
        self.document_count = 0

    def save_index(self, crawl_results):
        """
        Builds TF-IDF inverted index from crawl results.
        Only stores the inverted index, NOT the full quotes.
        Uses page numbers as document IDs.
        
        Args:
            crawl_results: List of dicts with 'page_number', 'url', 'author', 'text'
        """
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Group quotes by page number
        pages_data = defaultdict(list)
        for result in crawl_results:
            page_num = str(result['page_number'])
            pages_data[page_num].append(result)
            # Store URL for this page
            if page_num not in self.page_urls:
                self.page_urls[page_num] = result['url']
        
        self.document_count = len(pages_data)
        
        # Build inverted index with TF-IDF
        self._build_tfidf_index(pages_data)

        # Save ONLY the inverted index and metadata (NO quotes)
        data_to_save = {
            "inverted_index": self.inverted_index,
            "tf_idf_scores": self.tf_idf_scores,
            "page_urls": self.page_urls,
            "document_count": self.document_count
        }
        
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2)
        
        return self.index_path

    def _build_tfidf_index(self, pages_data):
        """
        Builds inverted index with TF-IDF scores.
        
        Args:
            pages_data: Dict mapping page_number -> list of quotes on that page
        """
        # First pass: Build basic inverted index with term frequencies
        self.inverted_index = defaultdict(lambda: defaultdict(lambda: {"frequency": 0, "positions": []}))
        
        for page_num, quotes in pages_data.items():
            # Combine all quotes from this page
            page_text = " ".join([f"{q['author']} {q['text']}" for q in quotes])
            
            # Tokenize: lowercases everything and removes punctuation
            tokens = re.findall(r'\w+', page_text.lower())

            # Build inverted index with frequency and positions
            for pos, word in enumerate(tokens):
                self.inverted_index[word][page_num]["frequency"] += 1
                self.inverted_index[word][page_num]["positions"].append(pos)

        # Convert defaultdict to regular dict
        self.inverted_index = {k: dict(v) for k, v in self.inverted_index.items()}

        # Second pass: Calculate TF-IDF scores
        self.tf_idf_scores = {}
        
        for term, pages in self.inverted_index.items():
            self.tf_idf_scores[term] = {}
            
            # Document frequency: number of pages containing this term
            df = len(pages)
            
            # IDF = log(N / df) where N is total number of pages
            idf = math.log(self.document_count / df) if df > 0 else 0
            
            for page_num, stats in pages.items():
                # TF = frequency of term in page
                tf = stats["frequency"]
                
                # TF-IDF = TF * IDF
                tf_idf = tf * idf
                
                self.tf_idf_scores[term][page_num] = {
                    "tf": tf,
                    "idf": idf,
                    "tf_idf": tf_idf
                }

    def load_index(self):
        """Reads the inverted index JSON file."""
        if not os.path.exists(self.index_path):
            return None
        
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extract all data from the JSON
            self.inverted_index = data.get("inverted_index", {})
            self.tf_idf_scores = data.get("tf_idf_scores", {})
            self.page_urls = data.get("page_urls", {})
            self.document_count = data.get("document_count", 0)
            
            if not self.inverted_index:
                return []
            
            print(f"[+] Loaded index for {self.document_count} pages")
            print(f"[+] Index contains {len(self.inverted_index)} unique terms")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"[-] Error: Invalid JSON format in {self.index_path}: {e}")
            return None
        except Exception as e:
            print(f"[-] Error loading file: {e}")
            return None

    def get_inverted_index_for_word(self, word):
        """Returns the inverted index entry for a specific word."""
        word_lower = word.lower()
        
        if word_lower not in self.inverted_index:
            return None
        
        return {
            "term": word_lower,
            "document_frequency": len(self.inverted_index[word_lower]),
            "pages": self.inverted_index[word_lower],
            "tf_idf": self.tf_idf_scores.get(word_lower, {})
        }