import pytest
import os
from src.indexer import IndexManager

@pytest.fixture
def temp_index_manager(tmp_path):
    """Fixture to provide an IndexManager mapped to a safe, temporary directory."""
    manager = IndexManager()
    manager.data_dir = str(tmp_path)
    manager.data_path = os.path.join(manager.data_dir, "test_index.txt")
    return manager

class TestIndexManager:
    def test_save_and_load_success(self, temp_index_manager):
        """Test saving data to disk and loading it back into memory."""
        test_data = [
            {'author': 'Author A', 'text': 'This is a test quote.'},
            {'author': 'Author B', 'text': 'Another test, testing is good.'}
        ]
        
        # Save it
        saved_path = temp_index_manager.save_index(test_data)
        assert os.path.exists(saved_path)
        
        # Load it
        quotes = temp_index_manager.load_index()
        assert len(quotes) == 2
        
        # Check inverted index structure
        assert "test" in temp_index_manager.inverted_index
        assert temp_index_manager.inverted_index["test"] == {0, 1}
        assert "another" in temp_index_manager.inverted_index
        assert temp_index_manager.inverted_index["another"] == {1}

    def test_load_missing_file(self, temp_index_manager):
        """Test trying to load when no file exists yet."""
        # Ensure file doesn't exist
        if os.path.exists(temp_index_manager.data_path):
            os.remove(temp_index_manager.data_path)
            
        result = temp_index_manager.load_index()
        assert result is None

    def test_load_empty_file(self, temp_index_manager):
        """Test loading a file that exists but has absolutely no data in it."""
        with open(temp_index_manager.data_path, "w", encoding="utf-8") as f:
            f.write("   \n  ") # Write just whitespace
            
        quotes = temp_index_manager.load_index()
        
        # Should return an empty list, not crash
        assert quotes == []
        assert temp_index_manager.inverted_index == {}

    def test_load_corrupted_format(self, temp_index_manager):
        """Test a file that doesn't use our standard separator format."""
        with open(temp_index_manager.data_path, "w", encoding="utf-8") as f:
            f.write("Just some random text\nNo author here\nNothing makes sense.")
            
        # It shouldn't crash. It might load garbage, but shouldn't throw an unhandled exception.
        try:
            quotes = temp_index_manager.load_index()
            assert isinstance(quotes, list) 
        except Exception as e:
            pytest.fail(f"Loading corrupt data crashed the program: {e}")