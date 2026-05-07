"""
indexer.py - TF-IDF weighted inverted index manager.

Builds and manages a TF-IDF inverted index for efficient text search.
Groups multiple quotes per page, stores only the index structure (not full text),
and provides methods for saving, loading, and querying the index.

TF-IDF Formula: TF-IDF = TF × IDF where IDF = log(N / DF)

Example:
    >>> from indexer import IndexManager
    >>> manager = IndexManager()
    >>> manager.save_index(crawl_results)
    >>> manager.load_index()
    >>> word_info = manager.get_inverted_index_for_word("life")
"""

import os
import re
import json
import math
from typing import Dict, List, Any, Optional
from collections import defaultdict


class IndexManager:
    """
    Manages TF-IDF weighted inverted index for quote search.
    
    Handles building, saving, loading, and querying the index. Groups multiple
    quotes per page and stores only the index structure for efficient storage.
    
    Attributes:
        data_dir (str): Directory path for storing index files
        index_path (str): Full path to the JSON index file
        inverted_index (Dict): Maps terms to pages to frequency/position info
        tf_idf_scores (Dict): Maps terms to pages to TF-IDF scores
        page_urls (Dict[str, str]): Maps page numbers to URLs
        document_count (int): Total number of unique pages indexed
    
    Example:
        >>> manager = IndexManager()
        >>> manager.save_index(crawl_data)
        >>> manager.load_index()
        >>> 'life' in manager.inverted_index
        True
    """
    
    def __init__(self) -> None:
        """Initialize the IndexManager with default paths and empty structures."""
        self.data_dir: str = os.path.join(os.getcwd(), "..", "data")
        self.index_path: str = os.path.join(self.data_dir, "inverted_index.json")
        self.inverted_index: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.tf_idf_scores: Dict[str, Dict[str, Dict[str, float]]] = {}
        self.page_urls: Dict[str, str] = {}
        self.document_count: int = 0

    def save_index(self, crawl_results: List[Dict[str, Any]]) -> str:
        """
        Build TF-IDF inverted index from crawl results and save to disk.
        
        Processing steps:
        1. Groups quotes by page number
        2. Builds inverted index with term frequencies and positions
        3. Calculates TF-IDF scores for each term-page pair
        4. Saves index structure to JSON (excludes original quote text)
        
        Args:
            crawl_results (List[Dict[str, Any]]): List from crawler with keys:
                'page_number', 'url', 'author', 'text'
        
        Returns:
            str: Path to the saved index file
        
        Note:
            Creates data directory if it doesn't exist.
            Stores URLs but not original quote text.
        """
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Group quotes by page number
        pages_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        for result in crawl_results:
            page_num = str(result['page_number'])
            pages_data[page_num].append(result)
            
            if page_num not in self.page_urls:
                self.page_urls[page_num] = result['url']
        
        self.document_count = len(pages_data)
        
        # Build inverted index with TF-IDF
        self._build_tfidf_index(pages_data)

        # Save to JSON (excludes quote text)
        data_to_save: Dict[str, Any] = {
            "inverted_index": self.inverted_index,
            "tf_idf_scores": self.tf_idf_scores,
            "page_urls": self.page_urls,
            "document_count": self.document_count
        }
        
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2)
        
        return self.index_path

    def _build_tfidf_index(
        self,
        pages_data: Dict[str, List[Dict[str, Any]]]
    ) -> None:
        """
        Build inverted index with TF-IDF scores from grouped page data.
        
        Two-pass algorithm:
        Pass 1: Build basic inverted index with term frequencies
        Pass 2: Calculate TF-IDF scores using document frequencies
        
        Args:
            pages_data (Dict): Maps page numbers to lists of quotes
        
        Side Effects:
            Updates self.inverted_index and self.tf_idf_scores
        """
        # Pass 1: Build inverted index with frequencies
        temp_index: defaultdict = defaultdict(
            lambda: defaultdict(lambda: {"frequency": 0, "positions": []})
        )
        
        for page_num, quotes in pages_data.items():
            # Combine all quotes from this page
            page_text: str = " ".join([
                f"{q['author']} {q['text']}" for q in quotes
            ])
            
            # Tokenize: extract alphanumeric words in lowercase
            tokens: List[str] = re.findall(r'\w+', page_text.lower())

            # Build index with frequency and position tracking
            for pos, word in enumerate(tokens):
                temp_index[word][page_num]["frequency"] += 1
                temp_index[word][page_num]["positions"].append(pos)

        # Convert to regular dict
        self.inverted_index = {k: dict(v) for k, v in temp_index.items()}

        # Pass 2: Calculate TF-IDF scores
        self.tf_idf_scores = {}
        
        for term, pages in self.inverted_index.items():
            self.tf_idf_scores[term] = {}
            
            # Document Frequency: number of pages containing this term
            df: int = len(pages)
            
            # IDF = log(N / df)
            idf: float = math.log(self.document_count / df) if df > 0 else 0.0
            
            for page_num, stats in pages.items():
                tf: int = stats["frequency"]
                tf_idf: float = tf * idf
                
                self.tf_idf_scores[term][page_num] = {
                    "tf": tf,
                    "idf": idf,
                    "tf_idf": tf_idf
                }

    def load_index(self) -> Optional[bool]:
        """
        Load the inverted index from JSON file into memory.
        
        Returns:
            bool: True if loaded successfully, None if file doesn't exist
        
        Note:
            Prints loading statistics to console.
        """
        if not os.path.exists(self.index_path):
            return None
        
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data: Dict[str, Any] = json.load(f)
            
            # Restore data structures
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

    def get_inverted_index_for_word(
        self,
        word: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete index entry for a specific word.
        
        Args:
            word (str): The word to look up (case-insensitive)
        
        Returns:
            Dict[str, Any]: Dictionary with keys:
                'term', 'document_frequency', 'pages', 'tf_idf'
            Returns None if word not found.
        
        Example:
            >>> result = manager.get_inverted_index_for_word("life")
            >>> print(f"'{result['term']}' appears in "
            ...       f"{result['document_frequency']} pages")
        """
        word_lower: str = word.lower()
        
        if word_lower not in self.inverted_index:
            return None
        
        return {
            "term": word_lower,
            "document_frequency": len(self.inverted_index[word_lower]),
            "pages": self.inverted_index[word_lower],
            "tf_idf": self.tf_idf_scores.get(word_lower, {})
        }