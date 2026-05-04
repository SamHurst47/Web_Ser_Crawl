import cmd
import os
import argparse
import sys
from crawler import QuoteCrawler
from indexer import IndexManager
from search import SearchEngine

class SearchToolShell(cmd.Cmd):
    intro = "QUOTE SEARCH TOOL - CLI v1.0\nType 'help' to see available commands."
    prompt = 'search-tool> '
    
    def __init__(self):
        super().__init__()
        self.manager = IndexManager()
        self.engine = SearchEngine(self.manager)
        self.is_index_loaded = False

    # --- HELP DOCUMENTATION ---

    def help_build(self):
        print("\nUsage: build")
        print("Description: Crawls the website, builds the inverted index, and saves to ../data/inverted_index.json\n")

    def help_load(self):
        print("\nUsage: load")
        print("Description: Reads the saved inverted index from disk back into memory so you can search without crawling again.\n")

    def help_print(self):
        print("\nUsage: print <word>")
        print("Description: Displays the raw inverted index entry for a specific word.\n")

    def help_find(self):
        print("\nUsage: find <query>")
        print("Description: Finds quotes containing all words in the query (AND logic).")
        print("             Example: find good friends\n")

    def help_exit(self):
        print("\nUsage: exit")
        print("Description: Closes the application.\n")

    # --- COMMAND IMPLEMENTATIONS ---

    def do_build(self, arg):
        """Crawl the site, build the inverted index, and save to disk."""
        # Explicit warning about the required 6-second politeness delay
        print("[*] Starting crawl. This will take a few moments due to the required 6-second politeness delay between pages...")
        
        crawler = QuoteCrawler()
        results = crawler.crawl()
        
        if not results:
            print("[-] Error: No data found. Check your network connection.")
            return

        try:
            # Build the inverted index and save everything to a single JSON file
            saved_path = self.manager.save_index(results)
            # Auto-load after building
            self.manager.load_index()
            self.is_index_loaded = True
            print(f"[+] Build successful! {len(results)} quotes indexed and saved to:\n    {saved_path}")
        except Exception as e:
            print(f"[-] Critical Error saving file: {e}")

    def do_load(self, arg):
        """Read the previously saved inverted index from disk into memory."""
        if self.is_index_loaded:
            print("[-] Error: Load cannot be called twice. The index is already in memory.")
            return
        
        # Reads inverted_index.json back into self.manager.inverted_index and self.manager.quotes
        data = self.manager.load_index()
        if data is not None:
            print(f"[+] Loaded {len(data)} quotes into memory.")
            self.is_index_loaded = True
        else:
            print("[-] Load failed. Has 'build' been run yet? Please run the 'build' command to create an index if you have not already.")

    def do_print(self, arg):
        """Print inverted index for a word."""
        if not self.is_index_loaded:
            print("[-] Error: An index is not loaded. Please run the 'load' command first.")
            return
        
        if not arg:
            self.help_print()
            return

        word = arg.strip().lower()
        entry = self.manager.inverted_index.get(word, {})

        if not entry:
            print(f"[-] Word '{word}' not found in index.")
            return

        print(f"Word: '{word}'")
        for doc_id, stats in entry.items():
            print(f"  Quote ID {doc_id} -> frequency: {stats['frequency']}, positions: {stats['positions']}")

    def do_find(self, arg):
        """Find quotes containing all words: find word1 word2 ..."""
        if not self.is_index_loaded:
            print("[-] Error: An index is not loaded. Please run the 'load' command first.")
            return

        if not arg:
            print("[-] Error: Please provide a search term.")
            return

        # Pass the full string "good friends" to the engine
        matches = self.engine.execute_find(arg)

        if not matches:
            print(f"[-] No quotes found containing all words in: '{arg}'")
        else:
            print(f"[+] Found {len(matches)} matches:")
            for q_id in matches:
                quote = self.manager.quotes[int(q_id)]
                print(f"\n--- Quote ID: {q_id} ---")
                print(f"Author: {quote['author']}")
                print(f"Quote: {quote['text']}")

    def do_exit(self, arg):
        """Exit the shell."""
        print("Goodbye!")
        return True

    def do_EOF(self, arg):
        return True

    def emptyline(self):
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Quote Search Tool")
    args = parser.parse_args()
    # Then start the interactive shell
    SearchToolShell().cmdloop()