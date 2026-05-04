import os
import sys
import json
from indexer import IndexManager

def test_save_and_load():
    """Test that we can save and load the inverted index correctly"""
    print("[TEST] Testing save and load functionality...")
    
    # Sample data
    sample_quotes = [
        {"author": "Albert Einstein", "text": "Life is beautiful"},
        {"author": "Maya Angelou", "text": "Life is a journey"},
        {"author": "Mark Twain", "text": "The beautiful journey of life"}
    ]
    
    # Initialize manager
    manager = IndexManager()
    
    # Save the index
    print("[TEST] Saving sample quotes...")
    saved_path = manager.save_index(sample_quotes)
    print(f"[TEST] Saved to: {saved_path}")
    
    # Verify the file exists
    if not os.path.exists(saved_path):
        print("[FAIL] Index file was not created!")
        return False
    
    # Load the JSON and verify structure
    print("[TEST] Verifying JSON structure...")
    with open(saved_path, 'r') as f:
        data = json.load(f)
    
    if "quotes" not in data:
        print("[FAIL] 'quotes' key missing from JSON!")
        return False
    
    if "inverted_index" not in data:
        print("[FAIL] 'inverted_index' key missing from JSON!")
        return False
    
    if len(data["quotes"]) != 3:
        print(f"[FAIL] Expected 3 quotes, got {len(data['quotes'])}")
        return False
    
    print("[TEST] JSON structure is correct!")
    print(f"[TEST] Found {len(data['inverted_index'])} unique terms in index")
    
    # Create a new manager instance and load
    print("[TEST] Loading index into new manager instance...")
    manager2 = IndexManager()
    loaded_quotes = manager2.load_index()
    
    if loaded_quotes is None:
        print("[FAIL] Failed to load index!")
        return False
    
    if len(loaded_quotes) != 3:
        print(f"[FAIL] Expected 3 loaded quotes, got {len(loaded_quotes)}")
        return False
    
    # Verify the inverted index was loaded
    if not manager2.inverted_index:
        print("[FAIL] Inverted index is empty after loading!")
        return False
    
    print(f"[TEST] Successfully loaded {len(loaded_quotes)} quotes")
    print(f"[TEST] Inverted index contains {len(manager2.inverted_index)} terms")
    
    # Test a specific word
    if "life" not in manager2.inverted_index:
        print("[FAIL] Word 'life' should be in the index!")
        return False
    
    life_entries = manager2.inverted_index["life"]
    print(f"[TEST] Word 'life' appears in {len(life_entries)} quotes")
    
    # Verify all three quotes contain "life"
    if len(life_entries) != 3:
        print(f"[FAIL] Expected 'life' in 3 quotes, found in {len(life_entries)}")
        return False
    
    print("[PASS] All tests passed!")
    
    # Print sample of the index structure
    print("\n[TEST] Sample of inverted index structure:")
    print(json.dumps({"life": manager2.inverted_index["life"]}, indent=2))
    
    return True

if __name__ == "__main__":
    success = test_save_and_load()
    sys.exit(0 if success else 1)