import cmd
import argparse
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
        print("Description: Crawls the website, builds the TF-IDF inverted index, and saves to ../data/inverted_index.json\n")

    def help_load(self):
        print("\nUsage: load")
        print("Description: Loads the inverted index from the file system.\n")

    def help_print(self):
        print("\nUsage: print <word>")
        print("Description: Prints the inverted index for a particular word, including TF-IDF scores.\n")

    def help_find(self):
        print("\nUsage: find <query>")
        print("Description: Finds pages containing the query words, ranked by TF-IDF relevance.")
        print("             Example: find indifference")
        print("             Example: find good friends\n")

    def help_exit(self):
        print("\nUsage: exit")
        print("Description: Closes the application.\n")

    # --- COMMAND IMPLEMENTATIONS ---

    def do_build(self, arg):
        """Crawl the site, build the TF-IDF inverted index, and save to disk."""
        print("[*] Starting crawl. This will take a few moments due to the required 6-second politeness delay between pages...")
        
        crawler = QuoteCrawler()
        results = crawler.crawl()
        
        if not results:
            print("[-] Error: No data found. Check your network connection.")
            return

        try:
            # Build the TF-IDF inverted index and save (quotes NOT saved)
            saved_path = self.manager.save_index(results)
            # Auto-load after building
            self.manager.load_index()
            self.is_index_loaded = True
            print(f"[+] Build successful! Indexed {len(results)} pages and saved to:\n    {saved_path}")
            print(f"[+] Note: Only the inverted index is stored, not the full page content.")
        except Exception as e:
            print(f"[-] Critical Error saving file: {e}")

    def do_load(self, arg):
        """Load the inverted index from the file system."""
        if self.is_index_loaded:
            print("[-] Error: Load cannot be called twice. The index is already in memory.")
            return
        
        result = self.manager.load_index()
        if result is not None:
            self.is_index_loaded = True
        else:
            print("[-] Load failed. Has 'build' been run yet? Please run the 'build' command to create an index.")

    def do_print(self, arg):
        """Print inverted index for a word with TF-IDF scores."""
        if not self.is_index_loaded:
            print("[-] Error: An index is not loaded. Please run the 'load' command first.")
            return
        
        if not arg:
            self.help_print()
            return

        word = arg.strip()
        index_entry = self.manager.get_inverted_index_for_word(word)

        if not index_entry:
            print(f"[-] Word '{word}' not found in index.")
            return

        print(f"\nInverted Index for: '{index_entry['term']}'")
        print(f"Document Frequency: {index_entry['document_frequency']} (appears in {index_entry['document_frequency']} pages)")
        print(f"\nPage Details:")
        print("-" * 80)
        
        # Sort pages by TF-IDF score (descending)
        pages_with_scores = []
        for page_num, stats in index_entry['pages'].items():
            tf_idf_info = index_entry['tf_idf'].get(page_num, {})
            page_url = self.manager.page_urls.get(page_num, f"Unknown URL")
            pages_with_scores.append((page_num, page_url, stats, tf_idf_info))
        
        # Sort by TF-IDF score
        pages_with_scores.sort(key=lambda x: x[3].get('tf_idf', 0), reverse=True)
        
        for page_num, page_url, stats, tf_idf_info in pages_with_scores:
            print(f"Page {page_num}")
            print(f"  URL: {page_url}")
            print(f"  Term Frequency (TF): {stats['frequency']}")
            print(f"  Positions: {stats['positions']}")
            if tf_idf_info:
                print(f"  IDF: {tf_idf_info.get('idf', 0):.4f}")
                print(f"  TF-IDF Score: {tf_idf_info.get('tf_idf', 0):.4f}")
            print()

    def do_find(self, arg):
        """Find pages containing query words, ranked by TF-IDF relevance."""
        if not self.is_index_loaded:
            print("[-] Error: An index is not loaded. Please run the 'load' command first.")
            return

        if not arg:
            print("[-] Error: Please provide a search term.")
            return

        # Search and get ranked results
        matches = self.engine.execute_find(arg)

        if not matches:
            print(f"[-] No pages found containing all words in: '{arg}'")
        else:
            print(f"[+] Found {len(matches)} pages (ranked by relevance):")
            for rank, page_num in enumerate(matches, 1):
                page_url = self.manager.page_urls.get(page_num, f"Unknown URL")
                print(f"[{rank}] Page {page_num}: {page_url}")

    def do_exit(self, arg):
        """Exit the shell."""
        print("Goodbye!")
        return True

    def do_EOF(self, arg):
        return True

    def emptyline(self):
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Quote Search Tool with TF-IDF")
    args = parser.parse_args()
    SearchToolShell().cmdloop()