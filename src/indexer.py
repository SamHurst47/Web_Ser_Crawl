import os
import re

class IndexManager:
    def __init__(self):
        # Safely points to ../data/index.txt regardless of operating system
        self.data_dir = os.path.join(os.getcwd(), "..", "data")
        self.data_path = os.path.join(self.data_dir, "index.txt")
        self.quotes = []          
        self.inverted_index = {}  

    def save_index(self, results):
        """Saves the crawled results to the file system."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        with open(self.data_path, "w", encoding="utf-8") as f:
            for item in results:
                f.write(f"AUTHOR: {item['author']}\nQUOTE: {item['text']}\n{'-'*20}\n")
        
        return self.data_path

    def load_index(self):
        """Reads index.txt and builds the Inverted Index mapping."""
        if not os.path.exists(self.data_path):
            return None
        
        self.quotes = []
        self.inverted_index = {}
        
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Handle completely empty files gracefully
                if not content.strip():
                    return []

                entries = content.split("-" * 20)
                
                for idx, entry in enumerate(entries):
                    clean_entry = entry.strip()
                    if not clean_entry: 
                        continue
                    
                    self.quotes.append(clean_entry)
                    
                    # Tokenize: lowercases everything and removes punctuation
                    words = re.findall(r'\w+', clean_entry.lower())
                    
                    # Build Inverted Index using Sets (required for AND logic later)
                    for word in set(words):
                        if word not in self.inverted_index:
                            self.inverted_index[word] = set()
                        self.inverted_index[word].add(idx)
                        
            return self.quotes
            
        except Exception as e:
            print(f"[-] Error loading file: {e}")
            return None