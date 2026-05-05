import os
import sys
import json
import pytest
import tempfile
import shutil

# Add parent directory to path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.indexer import IndexManager
from src.search import SearchEngine


@pytest.fixture
def temp_data_dir():
    """Create a temporary data directory for testing"""
    temp_dir = tempfile.mkdtemp()
    original_getcwd = os.getcwd
    os.getcwd = lambda: temp_dir
    yield temp_dir
    os.getcwd = original_getcwd
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_crawl_results():
    """Fixture providing sample crawl data with page numbers"""
    return [
        {"page_number": 1, "url": "https://example.com/", "author": "Albert Einstein", "text": "Life is beautiful"},
        {"page_number": 1, "url": "https://example.com/", "author": "Maya Angelou", "text": "Life is a journey"},
        {"page_number": 2, "url": "https://example.com/page/2/", "author": "Mark Twain", "text": "The beautiful journey of life"},
        {"page_number": 2, "url": "https://example.com/page/2/", "author": "Oscar Wilde", "text": "Be yourself everyone else is taken"}
    ]


@pytest.fixture
def manager(temp_data_dir):
    """Fixture providing a fresh IndexManager instance"""
    return IndexManager()


@pytest.fixture
def loaded_manager(manager, sample_crawl_results):
    """Fixture providing a manager with sample data loaded"""
    manager.save_index(sample_crawl_results)
    manager.load_index()
    return manager


class TestSaveAndLoad:
    """Test suite for save and load functionality"""
    
    def test_save_creates_file(self, manager, sample_crawl_results, temp_data_dir):
        """Test that saving creates the JSON file"""
        saved_path = manager.save_index(sample_crawl_results)
        assert os.path.exists(saved_path), "Index file was not created"
    
    def test_json_structure(self, manager, sample_crawl_results, temp_data_dir):
        """Test that saved JSON has correct structure"""
        saved_path = manager.save_index(sample_crawl_results)
        
        with open(saved_path, 'r') as f:
            data = json.load(f)
        
        assert "inverted_index" in data, "'inverted_index' key missing from JSON"
        assert "tf_idf_scores" in data, "'tf_idf_scores' key missing from JSON"
        assert "page_urls" in data, "'page_urls' key missing from JSON"
        assert "document_count" in data, "'document_count' key missing"
        
        # Should NOT have quotes array
        assert "quotes" not in data, "'quotes' should not be stored"
    
    def test_pages_grouped_correctly(self, manager, sample_crawl_results, temp_data_dir):
        """Test that quotes are grouped by page number"""
        manager.save_index(sample_crawl_results)
        
        # Should have 2 pages (page 1 and page 2)
        assert manager.document_count == 2, f"Expected 2 pages, got {manager.document_count}"
        
        # Check page URLs are stored
        assert "1" in manager.page_urls
        assert "2" in manager.page_urls
    
    def test_load_index(self, manager, sample_crawl_results, temp_data_dir):
        """Test that index is loaded correctly"""
        manager.save_index(sample_crawl_results)
        result = manager.load_index()
        
        assert result is not None, "Failed to load index"
        assert len(manager.inverted_index) > 0, "Inverted index is empty"
        assert len(manager.tf_idf_scores) > 0, "TF-IDF scores are empty"
    
    def test_load_nonexistent_file(self, manager):
        """Test loading when file doesn't exist"""
        manager.index_path = "/tmp/nonexistent_file_12345.json"
        result = manager.load_index()
        assert result is None, "Should return None for non-existent file"


class TestPageCombination:
    """Test that multiple quotes on same page are combined"""
    
    def test_words_from_different_quotes_same_page(self, loaded_manager):
        """Test that words from different quotes on same page are indexed together"""
        # Page 1 has two quotes:
        # - "Life is beautiful" (Albert Einstein)
        # - "Life is a journey" (Maya Angelou)
        
        # "beautiful" should be on page 1
        assert "beautiful" in loaded_manager.inverted_index
        assert "1" in loaded_manager.inverted_index["beautiful"]
        
        # "journey" should be on page 1 (from second quote)
        assert "journey" in loaded_manager.inverted_index
        assert "1" in loaded_manager.inverted_index["journey"]
    
    def test_page_contains_both_quotes(self, loaded_manager):
        """Test that page 1 is indexed with content from both quotes"""
        # "albert" and "maya" should both be on page 1
        assert "albert" in loaded_manager.inverted_index
        assert "1" in loaded_manager.inverted_index["albert"]
        
        assert "maya" in loaded_manager.inverted_index
        assert "1" in loaded_manager.inverted_index["maya"]


class TestSearchFunctionality:
    """Test suite for search operations with page-based indexing"""
    
    def test_search_single_word(self, loaded_manager):
        """Test searching for a single word"""
        engine = SearchEngine(loaded_manager)
        results = engine.execute_find("life")
        
        # "life" appears on both pages
        assert len(results) == 2, f"Expected 2 results for 'life', got {len(results)}"
        assert "1" in results or "2" in results
    
    def test_search_words_from_different_quotes_same_page(self, loaded_manager):
        """Test AND search where words are in different quotes on same page"""
        engine = SearchEngine(loaded_manager)
        
        # Page 1 has:
        # - Quote 1: "Life is beautiful"
        # - Quote 2: "Life is a journey"
        # So "beautiful" and "journey" are on same page but different quotes
        
        results = engine.execute_find("beautiful journey")
        
        # Should return page 1 (has both words, different quotes)
        assert len(results) >= 1, "Should find page with both words"
        assert "1" in results, "Page 1 should be in results"
    
    def test_search_nonexistent_word(self, loaded_manager):
        """Test searching for word not in index"""
        engine = SearchEngine(loaded_manager)
        results = engine.execute_find("python")
        assert len(results) == 0, f"Expected 0 results for 'python', got {len(results)}"
    
    def test_search_and_logic(self, loaded_manager):
        """Test that AND logic works - returns only pages with ALL words"""
        engine = SearchEngine(loaded_manager)
        
        # "beautiful" is on pages 1 and 2
        # "journey" is on pages 1 and 2
        # Both should return both pages
        results = engine.execute_find("beautiful journey")
        assert len(results) == 2, "Should return pages with both words"
    
    def test_search_case_insensitive(self, loaded_manager):
        """Test that search is case-insensitive"""
        engine = SearchEngine(loaded_manager)
        results_lower = engine.execute_find("life")
        results_upper = engine.execute_find("LIFE")
        results_mixed = engine.execute_find("LiFe")
        
        assert results_lower == results_upper == results_mixed, "Search is not case-insensitive"


class TestTFIDFScores:
    """Test suite for TF-IDF calculation"""
    
    def test_tfidf_scores_exist(self, loaded_manager):
        """Test that TF-IDF scores are calculated"""
        assert len(loaded_manager.tf_idf_scores) > 0, "No TF-IDF scores calculated"
        
        # Check structure
        for term, pages in loaded_manager.tf_idf_scores.items():
            for page_id, scores in pages.items():
                assert "tf" in scores
                assert "idf" in scores
                assert "tf_idf" in scores
    
    def test_common_word_lower_idf(self, loaded_manager):
        """Test that common words have lower IDF"""
        # "life" appears on both pages (common)
        # "yourself" appears on only page 2 (rare)
        
        if "life" in loaded_manager.tf_idf_scores and "yourself" in loaded_manager.tf_idf_scores:
            life_idf = list(loaded_manager.tf_idf_scores["life"].values())[0]["idf"]
            yourself_idf = list(loaded_manager.tf_idf_scores["yourself"].values())[0]["idf"]
            
            assert yourself_idf > life_idf, "Rare word should have higher IDF than common word"
    
    def test_frequency_affects_tf(self, loaded_manager):
        """Test that word frequency affects TF score"""
        # "life" appears multiple times on pages
        if "life" in loaded_manager.inverted_index:
            for page_id, stats in loaded_manager.inverted_index["life"].items():
                tf = loaded_manager.tf_idf_scores["life"][page_id]["tf"]
                assert tf == stats["frequency"], "TF should equal frequency"


class TestPrintCommand:
    """Test the get_inverted_index_for_word method"""
    
    def test_print_returns_correct_structure(self, loaded_manager):
        """Test that print command returns correct data structure"""
        result = loaded_manager.get_inverted_index_for_word("life")
        
        assert result is not None
        assert "term" in result
        assert "document_frequency" in result
        assert "pages" in result
        assert "tf_idf" in result
    
    def test_print_nonexistent_word(self, loaded_manager):
        """Test print with word not in index"""
        result = loaded_manager.get_inverted_index_for_word("nonexistent")
        assert result is None


class TestEdgeCases:
    """Test suite for edge cases"""
    
    def test_empty_crawl_results(self, manager, temp_data_dir):
        """Test saving empty crawl results"""
        manager.save_index([])
        manager.load_index()
        
        assert manager.document_count == 0
        assert len(manager.inverted_index) == 0
    
    def test_special_characters_stripped(self, manager, temp_data_dir):
        """Test that special characters are handled"""
        test_data = [
            {"page_number": 1, "url": "test.com", "author": "Test", "text": "Hello! How are you?"}
        ]
        manager.save_index(test_data)
        manager.load_index()
        
        # Should have alphanumeric words only
        assert "hello" in manager.inverted_index
        assert "how" in manager.inverted_index
        assert "!" not in manager.inverted_index
        assert "?" not in manager.inverted_index


if __name__ == "__main__":
    pytest.main([__file__, "-v"])