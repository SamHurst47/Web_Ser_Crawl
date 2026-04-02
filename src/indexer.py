import os
import re

class IndexManager:
    def __init__(self):
        self.data_path = os.path.join(os.getcwd(), "..", "data", "index.txt")
        self.quotes = []          # List of raw quotes
        self.inverted_index = {}  # Word -> List of Quote IDs

    def load_index(self):
        """Loads index and builds the inverted mapping."""
        if not os.path.exists(self.data_path):
            return None
        
        self.quotes = []
        self.inverted_index = {}
        
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                # Split by the separator we used in 'build'
                content = f.read().split("-" * 20)
                for idx, entry in enumerate(content):
                    clean_entry = entry.strip()
                    if not clean_entry: continue
                    
                    self.quotes.append(clean_entry)
                    
                    # Tokenize words (lowercase, alphanumeric only)
                    words = re.findall(r'\w+', clean_entry.lower())
                    for word in set(words): # 'set' prevents duplicate IDs for same word in one quote
                        if word not in self.inverted_index:
                            self.inverted_index[word] = []
                        self.inverted_index[word].append(idx)
            return self.quotes
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_word_index(self, word):
        """Returns the list of quote IDs containing the word."""
        return self.inverted_index.get(word.lower(), [])