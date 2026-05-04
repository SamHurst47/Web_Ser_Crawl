import os
import re
import json
from collections import defaultdict

class IndexManager:
    def __init__(self):
        # Only need the inverted_index.json file now
        self.data_dir = os.path.join(os.getcwd(), "..", "data")
        self.index_path = os.path.join(self.data_dir, "inverted_index.json")
        self.quotes = []
        self.inverted_index = {}

    def save_index(self, results):
        """Saves the crawled results and builds inverted index in a single JSON file."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Store quotes as a list
        self.quotes = results
        
        # Build inverted index
        self.inverted_index = defaultdict(lambda: defaultdict(lambda: {"frequency": 0, "positions": []}))
        
        for idx, quote in enumerate(results):
            # Tokenize author + text: lowercases everything and removes punctuation
            searchable = f"{quote['author']} {quote['text']}"
            tokens = re.findall(r'\w+', searchable.lower())

            # Build Inverted Index with frequency and positions per word per doc
            for pos, word in enumerate(tokens):
                self.inverted_index[word][str(idx)]["frequency"] += 1
                self.inverted_index[word][str(idx)]["positions"].append(pos)

        # Convert defaultdict to regular dict for JSON serialization
        self.inverted_index = {k: dict(v) for k, v in self.inverted_index.items()}

        # Save everything to a single JSON file with both quotes and index
        data_to_save = {
            "quotes": self.quotes,
            "inverted_index": self.inverted_index
        }
        
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2)
        
        return self.index_path

    def load_index(self):
        """Reads the inverted index JSON file and reconstructs quotes and index."""
        if not os.path.exists(self.index_path):
            return None
        
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Extract quotes and inverted index from the JSON
            self.quotes = data.get("quotes", [])
            self.inverted_index = data.get("inverted_index", {})
            
            if not self.quotes:
                return []
            
            print(f"[+] Loaded {len(self.quotes)} quotes from inverted index")
            print(f"[+] Index contains {len(self.inverted_index)} unique terms")
            
            return self.quotes
            
        except json.JSONDecodeError as e:
            print(f"[-] Error: Invalid JSON format in {self.index_path}: {e}")
            return None
        except Exception as e:
            print(f"[-] Error loading file: {e}")
            return None