import os
import sys
import json
import pytest

# Add parent directory to path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.indexer import IndexManager  
from src.search import SearchEngine


@pytest.fixture
def sample_quotes():
    """Fixture providing sample quote data"""
    return [
        {"author": "Albert Einstein", "text": "Life is beautiful"},
        {"author": "Maya Angelou", "text": "Life is a journey"},
        {"author": "Mark Twain", "text": "The beautiful journey of life"}
    ]


@pytest.fixture
def manager():
    """Fixture providing a fresh IndexManager instance"""
    return IndexManager()


@pytest.fixture
def loaded_manager(manager, sample_quotes):
    """Fixture providing a manager with sample data loaded"""
    manager.save_index(sample_quotes)
    manager.load_index()
    return manager


class TestSaveAndLoad:
    """Test suite for save and load functionality"""
    
    def test_save_creates_file(self, manager, sample_quotes):
        """Test that saving creates the JSON file"""
        saved_path = manager.save_index(sample_quotes)
        assert os.path.exists(saved_path), "Index file was not created"
    
    def test_json_structure(self, manager, sample_quotes):
        """Test that saved JSON has correct structure"""
        saved_path = manager.save_index(sample_quotes)
        
        with open(saved_path, 'r') as f:
            data = json.load(f)
        
        assert "quotes" in data, "'quotes' key missing from JSON"
        assert "inverted_index" in data, "'inverted_index' key missing from JSON"
        assert len(data["quotes"]) == 3, f"Expected 3 quotes, got {len(data['quotes'])}"
    
    def test_load_quotes(self, manager, sample_quotes):
        """Test that quotes are loaded correctly"""
        manager.save_index(sample_quotes)
        loaded_quotes = manager.load_index()
        
        assert loaded_quotes is not None, "Failed to load index"
        assert len(loaded_quotes) == 3, f"Expected 3 quotes, got {len(loaded_quotes)}"
    
    def test_load_inverted_index(self, manager, sample_quotes):
        """Test that inverted index is loaded correctly"""
        manager.save_index(sample_quotes)
        manager.load_index()
        
        assert manager.inverted_index, "Inverted index is empty after loading"
        assert len(manager.inverted_index) > 0, "No terms in inverted index"
    
    def test_load_nonexistent_file(self, manager):
        """Test loading when file doesn't exist"""
        manager.index_path = "/tmp/nonexistent_file_12345.json"
        result = manager.load_index()
        assert result is None, "Should return None for non-existent file"


class TestSearchFunctionality:
    """Test suite for search operations"""
    
    def test_search_single_word(self, loaded_manager):
        """Test searching for a single word"""
        engine = SearchEngine(loaded_manager)
        results = engine.execute_find("life")
        assert len(results) == 3, f"Expected 3 results for 'life', got {len(results)}"
    
    def test_search_multiple_words_and(self, loaded_manager):
        """Test AND search with multiple words"""
        engine = SearchEngine(loaded_manager)
        results = engine.execute_find("life journey")
        assert len(results) == 2, f"Expected 2 results for 'life journey', got {len(results)}"
    
    def test_search_nonexistent_word(self, loaded_manager):
        """Test searching for word not in index"""
        engine = SearchEngine(loaded_manager)
        results = engine.execute_find("python")
        assert len(results) == 0, f"Expected 0 results for 'python', got {len(results)}"
    
    def test_search_author(self, loaded_manager):
        """Test searching by author name"""
        engine = SearchEngine(loaded_manager)
        results = engine.execute_find("Einstein")
        assert len(results) == 1, f"Expected 1 result for 'Einstein', got {len(results)}"
        
        quote = loaded_manager.quotes[int(results[0])]
        assert quote['author'] == "Albert Einstein", f"Wrong author: {quote['author']}"
    
    def test_search_case_insensitive(self, loaded_manager):
        """Test that search is case-insensitive"""
        engine = SearchEngine(loaded_manager)
        results_lower = engine.execute_find("life")
        results_upper = engine.execute_find("LIFE")
        results_mixed = engine.execute_find("LiFe")
        
        assert results_lower == results_upper == results_mixed, "Search is not case-insensitive"
    
    def test_search_empty_query(self, loaded_manager):
        """Test searching with empty query"""
        engine = SearchEngine(loaded_manager)
        results = engine.execute_find("")
        assert len(results) == 0, "Empty query should return no results"


class TestFrequencyAndPositions:
    """Test suite for word frequency and position tracking"""
    
    def test_word_appears_in_all_quotes(self, loaded_manager):
        """Test that 'life' appears in all 3 quotes"""
        life_data = loaded_manager.inverted_index.get("life", {})
        assert len(life_data) == 3, f"Expected 'life' in 3 quotes, got {len(life_data)}"
    
    def test_frequency_matches_positions(self, loaded_manager):
        """Test that frequency count matches number of positions"""
        life_data = loaded_manager.inverted_index.get("life", {})
        
        for doc_id, stats in life_data.items():
            freq = stats["frequency"]
            positions = stats["positions"]
            assert freq == len(positions), f"Frequency mismatch in quote {doc_id}"
    
    def test_beautiful_appears_twice(self, loaded_manager):
        """Test that 'beautiful' appears in exactly 2 quotes"""
        beautiful_data = loaded_manager.inverted_index.get("beautiful", {})
        assert len(beautiful_data) == 2, f"Expected 'beautiful' in 2 quotes, got {len(beautiful_data)}"
    
    def test_positions_are_integers(self, loaded_manager):
        """Test that all positions are integers"""
        for word, docs in loaded_manager.inverted_index.items():
            for doc_id, stats in docs.items():
                for pos in stats["positions"]:
                    assert isinstance(pos, int), f"Position {pos} is not an integer"


class TestEmptyAndEdgeCases:
    """Test suite for empty and edge cases"""
    
    def test_empty_quotes_list(self, manager):
        """Test saving and loading empty quotes list"""
        manager.save_index([])
        quotes = manager.load_index()
        
        assert quotes is not None, "load_index() returned None for empty list"
        assert len(quotes) == 0, f"Expected 0 quotes, got {len(quotes)}"
        assert len(manager.inverted_index) == 0, f"Expected empty index, got {len(manager.inverted_index)} terms"
    
    def test_quote_with_special_characters(self, manager):
        """Test handling quotes with special characters"""
        special_quotes = [
            {"author": "Test Author", "text": "Hello! How are you? I'm fine."}
        ]
        manager.save_index(special_quotes)
        manager.load_index()
        
        # Should only extract alphanumeric words
        assert "hello" in manager.inverted_index
        assert "how" in manager.inverted_index
        assert "!" not in manager.inverted_index
        assert "?" not in manager.inverted_index
    
    def test_quote_with_numbers(self, manager):
        """Test handling quotes with numbers"""
        number_quotes = [
            {"author": "Test Author", "text": "There are 3 ways to do this"}
        ]
        manager.save_index(number_quotes)
        manager.load_index()
        
        assert "3" in manager.inverted_index
        assert "ways" in manager.inverted_index


class TestDataIntegrity:
    """Test suite for data integrity"""
    
    def test_quotes_preserved_after_save_load(self, manager, sample_quotes):
        """Test that quote data is preserved exactly after save/load cycle"""
        manager.save_index(sample_quotes)
        loaded_quotes = manager.load_index()
        
        for i, (original, loaded) in enumerate(zip(sample_quotes, loaded_quotes)):
            assert original["author"] == loaded["author"], f"Author mismatch at index {i}"
            assert original["text"] == loaded["text"], f"Text mismatch at index {i}"
    
    def test_inverted_index_consistency(self, loaded_manager):
        """Test that inverted index is internally consistent"""
        for word, docs in loaded_manager.inverted_index.items():
            for doc_id, stats in docs.items():
                # Check that doc_id is valid
                doc_id_int = int(doc_id)
                assert 0 <= doc_id_int < len(loaded_manager.quotes), f"Invalid doc_id: {doc_id}"
                
                # Check that the word actually appears in the quote
                quote = loaded_manager.quotes[doc_id_int]
                searchable = f"{quote['author']} {quote['text']}".lower()
                assert word in searchable, f"Word '{word}' not found in quote {doc_id}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])