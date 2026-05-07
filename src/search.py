"""
search.py - Search engine with TF-IDF ranking and query suggestions.

Implements search functionality over a TF-IDF weighted inverted index.
Supports AND-logic multi-word queries, ranks results by relevance, and
provides spell checking for misspelled query terms.

Example:
    >>> from search import SearchEngine
    >>> from indexer import IndexManager
    >>> manager = IndexManager()
    >>> manager.load_index()
    >>> engine = SearchEngine(manager)
    >>> results = engine.execute_find("good friends")
    >>> suggestions = engine.get_suggestions("frends")
"""

import re
from typing import List, Dict, Set

from src.spellcheck import get_query_suggestions


class SearchEngine:
    """
    Search engine with TF-IDF ranking and spell checking capabilities.
    
    Provides search functionality over a TF-IDF weighted inverted index.
    Implements AND-logic for multi-word queries (all words must appear on
    a page) and ranks results by relevance using TF-IDF scores.
    
    Attributes:
        manager: IndexManager instance containing the inverted index
    
    Example:
        >>> engine = SearchEngine(manager)
        >>> results = engine.execute_find("life beautiful")
        >>> len(results) >= 0
        True
    """
    
    def __init__(self, index_manager) -> None:
        """
        Initialize the SearchEngine with an IndexManager.
        
        Args:
            index_manager: IndexManager instance with loaded inverted index
        """
        self.manager = index_manager

    def execute_find(self, query: str) -> List[str]:
        """
        Find pages containing ALL query words, ranked by TF-IDF relevance.
        
        Implements AND-logic search:
        1. Tokenizes query into words
        2. Finds pages containing ALL words (intersection)
        3. Calculates relevance scores (sum of TF-IDF values)
        4. Returns page IDs sorted by relevance (descending)
        
        Args:
            query (str): Search query. Punctuation removed, case ignored.
        
        Returns:
            List[str]: Page IDs sorted by relevance (highest first).
                Empty list if no pages contain all query words.
        
        Examples:
            >>> results = engine.execute_find("life")
            >>> isinstance(results, list)
            True
            >>> results = engine.execute_find("good friends")
            >>> # Returns only pages with BOTH words
        
        Note:
            Query is case-insensitive and punctuation is removed.
            Words not in index cause zero results (AND logic).
        """
        # Tokenize query
        query_words: List[str] = re.findall(r'\w+', query.lower())
        
        if not query_words:
            return []

        # Initialize with pages containing first word
        if query_words[0] in self.manager.inverted_index:
            result_set: Set[str] = set(
                self.manager.inverted_index[query_words[0]].keys()
            )
        else:
            return []

        # Intersect with pages containing other words (AND logic)
        for word in query_words[1:]:
            if word in self.manager.inverted_index:
                word_pages: Set[str] = set(
                    self.manager.inverted_index[word].keys()
                )
                result_set = result_set.intersection(word_pages)
            else:
                return []
            
            # Early termination if no matches
            if not result_set:
                break

        if not result_set:
            return []

        # Calculate relevance scores
        scored_results: List[Dict[str, any]] = []
        
        for page_id in result_set:
            score: float = 0.0
            
            # Sum TF-IDF scores for all query words
            for word in query_words:
                if word in self.manager.tf_idf_scores:
                    if page_id in self.manager.tf_idf_scores[word]:
                        score += self.manager.tf_idf_scores[word][page_id]["tf_idf"]
            
            scored_results.append({
                "page_id": page_id,
                "score": score
            })
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        return [result["page_id"] for result in scored_results]
    
    def get_suggestions(self, query: str) -> Dict[str, List[str]]:
        """
        Get spelling suggestions for misspelled words in the query.
        
        Analyzes each word and provides suggestions for words not found in
        the index. Uses Levenshtein distance with max edit distance of 2.
        
        Args:
            query (str): Search query to analyze
        
        Returns:
            Dict[str, List[str]]: Maps misspelled words to suggestions.
                Format: {misspelled_word: [suggestion1, suggestion2, ...]}
                Empty dict if all words are in index.
        
        Examples:
            >>> suggestions = engine.get_suggestions("frends")
            >>> # Returns: {"frends": ["friends", "trends"]}
        
        Note:
            Maximum edit distance: 2
            Up to 3 suggestions per misspelled word
        """
        query_words: List[str] = re.findall(r'\w+', query.lower())
        
        if not query_words:
            return {}
        
        index_terms: Set[str] = set(self.manager.inverted_index.keys())
        
        return get_query_suggestions(query_words, index_terms, max_distance=2)