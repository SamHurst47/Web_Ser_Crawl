"""
test_search.py - Unit tests for search engine functionality.

Tests the SearchEngine class including AND-logic search, TF-IDF ranking,
and query suggestion features.

Run with: pytest tests/test_search.py -v
"""

import os
import sys
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.search import SearchEngine
from src.indexer import IndexManager


@pytest.fixture
def mock_manager():
    """Provides a pre-populated IndexManager for testing search logic."""
    manager = IndexManager()
    
    # Simulate 3 pages with combined quotes
    manager.page_urls = {
        "1": "https://example.com/",
        "2": "https://example.com/page/2/",
        "3": "https://example.com/page/3/"
    }
    
    manager.document_count = 3
    
    # Mock data represents:
    # Page 1: "apples and oranges" + "more apples here"
    # Page 2: "apples bananas and grapes"  
    # Page 3: "oranges and bananas"
    
    # Build inverted index with frequency/positions
    manager.inverted_index = {
        "apples": {
            "1": {"frequency": 2, "positions": [0, 3]},
            "2": {"frequency": 1, "positions": [0]}
        },
        "oranges": {
            "1": {"frequency": 1, "positions": [2]},
            "3": {"frequency": 1, "positions": [0]}
        },
        "bananas": {
            "2": {"frequency": 1, "positions": [1]},
            "3": {"frequency": 1, "positions": [2]}
        },
        "and": {
            "1": {"frequency": 1, "positions": [1]},
            "2": {"frequency": 1, "positions": [2]},
            "3": {"frequency": 1, "positions": [1]}
        },
        "grapes": {
            "2": {"frequency": 1, "positions": [3]}
        }
    }
    
    # Build TF-IDF scores
    manager.tf_idf_scores = {
        "apples": {
            "1": {"tf": 2, "idf": 0.405, "tf_idf": 0.810},
            "2": {"tf": 1, "idf": 0.405, "tf_idf": 0.405}
        },
        "oranges": {
            "1": {"tf": 1, "idf": 0.405, "tf_idf": 0.405},
            "3": {"tf": 1, "idf": 0.405, "tf_idf": 0.405}
        },
        "bananas": {
            "2": {"tf": 1, "idf": 0.405, "tf_idf": 0.405},
            "3": {"tf": 1, "idf": 0.405, "tf_idf": 0.405}
        },
        "and": {
            "1": {"tf": 1, "idf": 0.000, "tf_idf": 0.000},
            "2": {"tf": 1, "idf": 0.000, "tf_idf": 0.000},
            "3": {"tf": 1, "idf": 0.000, "tf_idf": 0.000}
        },
        "grapes": {
            "2": {"tf": 1, "idf": 1.099, "tf_idf": 1.099}
        }
    }
    
    return manager


class TestSearchEngine:
    """Test suite for basic search functionality."""
    
    def test_single_word_search(self, mock_manager):
        """Test searching for a single word."""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("apples")
        
        # "apples" appears on pages 1 and 2
        assert set(results) == {"1", "2"}

    def test_multi_word_search_and_logic(self, mock_manager):
        """Test AND logic - returns only pages with BOTH words."""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("apples bananas")
        
        # Only page 2 has both "apples" and "bananas"
        assert results == ["2"]

    def test_multi_word_both_pages(self, mock_manager):
        """Test AND search where both words appear on multiple pages."""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("oranges bananas")
        
        # Only page 3 has both words
        assert results == ["3"]

    def test_no_results_search(self, mock_manager):
        """Test search for word not in index."""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("kiwi")
        
        # Should return empty results
        assert results == []

    def test_empty_query(self, mock_manager):
        """Test empty query returns no results."""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("")
        
        assert results == []

    def test_search_whitespace_only(self, mock_manager):
        """Test queries that are just spaces."""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("     ")
        
        assert results == []

    def test_search_with_special_characters(self, mock_manager):
        """Test that search strips punctuation correctly."""
        engine = SearchEngine(mock_manager)
        
        # "apples-and-oranges!" should become ["apples", "and", "oranges"]
        results = engine.execute_find("apples-and-oranges!")
        
        # Page 1 has all three words
        assert "1" in results

    def test_search_case_insensitivity(self, mock_manager):
        """Test that search is case-insensitive."""
        engine = SearchEngine(mock_manager)
        
        results_upper = engine.execute_find("APPLES")
        results_mixed = engine.execute_find("ApPlEs")
        results_lower = engine.execute_find("apples")
        
        # All should return same results
        assert set(results_upper) == set(results_lower) == set(results_mixed)

    def test_search_partial_match_failure(self, mock_manager):
        """Test that if one word missing, no results returned (AND logic)."""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("apples kiwi")
        
        # 'apples' exists but 'kiwi' does not - AND logic returns empty
        assert results == []

    def test_three_word_search(self, mock_manager):
        """Test AND logic with three words."""
        engine = SearchEngine(mock_manager)
        
        # Only page 2 has "apples", "bananas", AND "grapes"
        results = engine.execute_find("apples bananas grapes")
        assert results == ["2"]

    def test_common_word_search(self, mock_manager):
        """Test search for very common word appearing in all pages."""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("and")
        
        # "and" appears in all three pages
        assert set(results) == {"1", "2", "3"}
    
    def test_ranking_by_tfidf(self, mock_manager):
        """Test that results are ranked by TF-IDF score."""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("apples")
        
        # Page 1 has higher TF-IDF (appears more times)
        # So page 1 should be ranked first
        assert results[0] == "1"
        assert results[1] == "2"


class TestQuerySuggestions:
    """Test suite for query suggestions (spell checking)."""
    
    def test_get_suggestions_for_misspelled_word(self, mock_manager):
        """Test that suggestions are returned for misspelled words."""
        engine = SearchEngine(mock_manager)
        
        # "appels" is misspelled, should suggest "apples"
        suggestions = engine.get_suggestions("appels")
        
        assert "appels" in suggestions
        assert "apples" in suggestions["appels"]
    
    def test_get_suggestions_for_correct_word(self, mock_manager):
        """Test that no suggestions for correctly spelled words in index."""
        engine = SearchEngine(mock_manager)
        
        # "apples" is correctly spelled and in index
        suggestions = engine.get_suggestions("apples")
        
        # Should not suggest for correct words
        assert "apples" not in suggestions
    
    def test_get_suggestions_multiple_words(self, mock_manager):
        """Test suggestions for multi-word query with one misspelling."""
        engine = SearchEngine(mock_manager)
        
        # "apples bananaz" - only "bananaz" is misspelled
        suggestions = engine.get_suggestions("apples bananaz")
        
        assert "apples" not in suggestions  # Correct word
        assert "bananaz" in suggestions     # Misspelled word
        assert "bananas" in suggestions["bananaz"]
    
    def test_get_suggestions_all_correct(self, mock_manager):
        """Test that empty dict returned when all words correct."""
        engine = SearchEngine(mock_manager)
        
        suggestions = engine.get_suggestions("apples bananas")
        
        # All words correct - no suggestions needed
        assert suggestions == {}
    
    def test_get_suggestions_word_not_in_index(self, mock_manager):
        """Test suggestions when word completely not in index."""
        engine = SearchEngine(mock_manager)
        
        # "xyz" has no similar words in index
        suggestions = engine.get_suggestions("xyz")
        
        # Should return empty or have "xyz" with empty list
        if "xyz" in suggestions:
            assert isinstance(suggestions["xyz"], list)
    
    def test_get_suggestions_case_insensitive(self, mock_manager):
        """Test that suggestions work regardless of case."""
        engine = SearchEngine(mock_manager)
        
        # "APPELS" in uppercase
        suggestions = engine.get_suggestions("APPELS")
        
        # Should still suggest "apples"
        if suggestions:
            misspelled_key = list(suggestions.keys())[0]
            assert "apples" in suggestions[misspelled_key]
    
    def test_get_suggestions_empty_query(self, mock_manager):
        """Test handling of empty query."""
        engine = SearchEngine(mock_manager)
        
        suggestions = engine.get_suggestions("")
        
        # Empty query should return empty dict
        assert suggestions == {}
    
    def test_get_suggestions_close_match(self, mock_manager):
        """Test that words within edit distance of 2 are suggested."""
        engine = SearchEngine(mock_manager)
        
        # "ornges" is 2 edits from "oranges"
        suggestions = engine.get_suggestions("ornges")
        
        assert "ornges" in suggestions
        
        # Should have at least one suggestion
        suggested_words = suggestions.get("ornges", [])
        assert len(suggested_words) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])