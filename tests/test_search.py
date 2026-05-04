import os
import sys
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.indexer import IndexManager  
from src.search import SearchEngine


@pytest.fixture
def mock_manager():
    """Provides a pre-populated IndexManager for testing search logic."""
    manager = IndexManager()
    manager.quotes = [
        {"author": "Author A", "text": "Quote zero about apples and oranges."},
        {"author": "Author B", "text": "Quote one about apples, bananas, and grapes."},
        {"author": "Author C", "text": "Quote two about oranges and bananas."}
    ]
    # Manually build the inverted index for testing (new format with frequency/positions)
    manager.inverted_index = {
        "apples": {
            "0": {"frequency": 1, "positions": [3]},
            "1": {"frequency": 1, "positions": [3]}
        },
        "oranges": {
            "0": {"frequency": 1, "positions": [5]},
            "2": {"frequency": 1, "positions": [4]}
        },
        "bananas": {
            "1": {"frequency": 1, "positions": [4]},
            "2": {"frequency": 1, "positions": [6]}
        },
        "and": {
            "0": {"frequency": 1, "positions": [4]},
            "1": {"frequency": 2, "positions": [5, 7]},
            "2": {"frequency": 1, "positions": [5]}
        }
    }
    return manager


class TestSearchEngine:
    def test_single_word_search(self, mock_manager):
        """Test searching for a single word"""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("apples")
        assert results == ["0", "1"]

    def test_multi_word_search_and_logic(self, mock_manager):
        """Test AND logic - should only return quotes with BOTH words"""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("apples bananas")
        assert results == ["1"]

    def test_no_results_search(self, mock_manager):
        """Test search for word not in index"""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("kiwi")
        assert results == []

    def test_empty_query(self, mock_manager):
        """Test empty query returns no results"""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("")
        assert results == []

    def test_search_whitespace_only(self, mock_manager):
        """Test queries that are just spaces"""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("     ")
        assert results == []

    def test_search_with_special_characters(self, mock_manager):
        """Test that search strips punctuation correctly"""
        engine = SearchEngine(mock_manager)
        # "apples-and-oranges!" should become ["apples", "and", "oranges"]
        results = engine.execute_find("apples-and-oranges!")
        assert results == ["0"]

    def test_search_case_insensitivity(self, mock_manager):
        """Test that search is case-insensitive"""
        engine = SearchEngine(mock_manager)
        results_upper = engine.execute_find("APPLES")
        results_mixed = engine.execute_find("ApPlEs")
        
        assert results_upper == ["0", "1"]
        assert results_mixed == ["0", "1"]

    def test_search_partial_match_failure(self, mock_manager):
        """Test that if one word missing, no results returned"""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("apples kiwi")
        # 'apples' exists, but 'kiwi' does not. AND logic = empty
        assert results == []

    def test_three_word_search(self, mock_manager):
        """Test AND logic with three words"""
        engine = SearchEngine(mock_manager)
        # Only quote 2 has "oranges" AND "bananas" AND "and"
        results = engine.execute_find("oranges bananas and")
        assert results == ["2"]

    def test_common_word_search(self, mock_manager):
        """Test search for very common word appearing in all quotes"""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("and")
        # "and" appears in all three quotes
        assert sorted(results) == ["0", "1", "2"]