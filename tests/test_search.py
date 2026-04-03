import pytest
from src.search import SearchEngine
from src.indexer import IndexManager

@pytest.fixture
def mock_manager():
    """Provides a pre-populated IndexManager for testing search logic."""
    manager = IndexManager()
    manager.quotes = [
        "Quote zero about apples and oranges.",
        "Quote one about apples, bananas, and grapes.",
        "Quote two about oranges and bananas."
    ]
    # Manually build the inverted index sets for testing
    manager.inverted_index = {
        "apples": {0, 1},
        "oranges": {0, 2},
        "bananas": {1, 2},
        "and": {0, 1, 2}
    }
    return manager

class TestSearchEngine:
    def test_single_word_search(self, mock_manager):
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("apples")
        assert results == [0, 1]

    def test_multi_word_search_and_logic(self, mock_manager):
        engine = SearchEngine(mock_manager)
        # Should only return quotes that have BOTH apples AND bananas
        results = engine.execute_find("apples bananas")
        assert results == [1]

    def test_no_results_search(self, mock_manager):
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("kiwi")
        assert results == []

    def test_empty_query(self, mock_manager):
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("")
        assert results == []

    def test_search_whitespace_only(self, mock_manager):
        """Test queries that are just spaces."""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("     ")
        assert results == []

    def test_search_with_special_characters(self, mock_manager):
        """Ensure search ignores punctuation and only looks at words."""
        engine = SearchEngine(mock_manager)
        # The user types "apples-and-oranges!" -> Should strip to ["apples", "and", "oranges"]
        results = engine.execute_find("apples-and-oranges!")
        assert results == [0]

    def test_search_case_insensitivity(self, mock_manager):
        """Test that uppercase and mixed case inputs work correctly."""
        engine = SearchEngine(mock_manager)
        results_upper = engine.execute_find("APPLES")
        results_mixed = engine.execute_find("ApPlEs")
        
        assert results_upper == [0, 1]
        assert results_mixed == [0, 1]

    def test_search_partial_match_failure(self, mock_manager):
        """If they search for 'apples kiwi', and 'kiwi' isn't there, return nothing."""
        engine = SearchEngine(mock_manager)
        results = engine.execute_find("apples kiwi")
        # 'apples' exists, but 'kiwi' does not. AND logic dictates it must return empty.
        assert results == []