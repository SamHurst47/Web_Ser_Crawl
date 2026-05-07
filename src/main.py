"""
main.py - Command-line interface for the Quote Search Tool.

Provides an interactive CLI for searching quotes using a TF-IDF weighted
inverted index. Supports building indexes, loading saved indexes, and
executing ranked searches with spell-check suggestions.

Commands:
    build - Crawl website and build TF-IDF index
    load - Load existing index from disk
    print <word> - Display inverted index entry for word
    find <query> - Search for pages containing query words
    exit - Quit the application

Example:
    $ python main.py
    search-tool> build
    search-tool> find good friends
    search-tool> exit
"""

import cmd
import argparse
from typing import Optional

from crawler import QuoteCrawler
from indexer import IndexManager
from search import SearchEngine


class SearchToolShell(cmd.Cmd):
    """
    Interactive command-line interface for the quote search system.
    
    Extends cmd.Cmd to provide an interactive shell with commands for
    crawling, indexing, and searching quotes.
    
    Attributes:
        intro (str): Welcome message displayed on startup
        prompt (str): Command prompt string
        manager (IndexManager): Manages the inverted index
        engine (SearchEngine): Executes search queries
        is_index_loaded (bool): Tracks whether index is loaded
    """
    
    intro: str = (
        "QUOTE SEARCH TOOL - CLI v1.0\n"
        "Type 'help' to see available commands."
    )
    prompt: str = 'search-tool> '
    
    def __init__(self) -> None:
        """Initialize the search tool shell with empty index."""
        super().__init__()
        self.manager: IndexManager = IndexManager()
        self.engine: SearchEngine = SearchEngine(self.manager)
        self.is_index_loaded: bool = False

    # === HELP DOCUMENTATION ===

    def help_build(self) -> None:
        """Display help text for the build command."""
        print("\nUsage: build")
        print("Description: Crawls the website, builds the TF-IDF inverted "
              "index, and saves to ../data/inverted_index.json\n")

    def help_load(self) -> None:
        """Display help text for the load command."""
        print("\nUsage: load")
        print("Description: Loads the inverted index from the file system.\n")

    def help_print(self) -> None:
        """Display help text for the print command."""
        print("\nUsage: print <word>")
        print("Description: Prints the inverted index for a word with TF-IDF scores.\n")

    def help_find(self) -> None:
        """Display help text for the find command."""
        print("\nUsage: find <query>")
        print("Description: Finds pages containing query words, ranked by TF-IDF.")
        print("             Example: find indifference")
        print("             Example: find good friends\n")

    def help_exit(self) -> None:
        """Display help text for the exit command."""
        print("\nUsage: exit")
        print("Description: Closes the application.\n")

    # === COMMAND IMPLEMENTATIONS ===

    def do_build(self, arg: str) -> None:
        """
        Crawl the website, build TF-IDF index, and save to disk.
        
        Steps:
        1. Crawls all pages (with 6-second politeness delay)
        2. Groups quotes by page number
        3. Builds TF-IDF weighted inverted index
        4. Saves to ../data/inverted_index.json
        5. Auto-loads index into memory
        
        Args:
            arg (str): Not used
        
        Note:
            Requires internet connection. Does not store original quote text.
        """
        print(
            "[*] Starting crawl. This will take a few moments due to the "
            "required 6-second politeness delay between pages..."
        )
        
        crawler: QuoteCrawler = QuoteCrawler()
        results: list = crawler.crawl()
        
        if not results:
            print("[-] Error: No data found. Check your network connection.")
            return

        try:
            saved_path: str = self.manager.save_index(results)
            self.manager.load_index()
            self.is_index_loaded = True
            
            print(
                f"[+] Build successful! Indexed {len(results)} quotes "
                f"and saved to:\n    {saved_path}"
            )
            print("[+] Note: Only the inverted index is stored, not the full "
                  "page content.")
                  
        except Exception as e:
            print(f"[-] Critical Error saving file: {e}")

    def do_load(self, arg: str) -> None:
        """
        Load the inverted index from file system into memory.
        
        Args:
            arg (str): Not used
        
        Note:
            Prevents loading if index already loaded.
        """
        if self.is_index_loaded:
            print("[-] Error: Load cannot be called twice. The index is "
                  "already in memory.")
            return
        
        result: Optional[bool] = self.manager.load_index()
        
        if result is not None:
            self.is_index_loaded = True
        else:
            print("[-] Load failed. Has 'build' been run yet? Please run the "
                  "'build' command to create an index.")

    def do_print(self, arg: str) -> None:
        """
        Print complete inverted index entry for a word with TF-IDF scores.
        
        Args:
            arg (str): The word to look up
        
        Output Format:
            Inverted Index for: 'word'
            Document Frequency: N
            Page Details:
            Page 10
              URL: https://...
              Term Frequency: 3
              Positions: [2, 7, 15]
              TF-IDF Score: 2.0794
        """
        if not self.is_index_loaded:
            print("[-] Error: An index is not loaded. Please run 'load' first.")
            return
        
        if not arg:
            self.help_print()
            return

        word: str = arg.strip()
        index_entry: Optional[dict] = self.manager.get_inverted_index_for_word(word)

        if not index_entry:
            print(f"[-] Word '{word}' not found in index.")
            return

        print(f"\nInverted Index for: '{index_entry['term']}'")
        print(f"Document Frequency: {index_entry['document_frequency']} "
              f"(appears in {index_entry['document_frequency']} pages)")
        print(f"\nPage Details:")
        print("-" * 80)
        
        # Prepare and sort pages by TF-IDF score
        pages_with_scores: list = []
        for page_num, stats in index_entry['pages'].items():
            tf_idf_info: dict = index_entry['tf_idf'].get(page_num, {})
            page_url: str = self.manager.page_urls.get(page_num, "Unknown URL")
            pages_with_scores.append((page_num, page_url, stats, tf_idf_info))
        
        pages_with_scores.sort(
            key=lambda x: x[3].get('tf_idf', 0),
            reverse=True
        )
        
        # Display results
        for page_num, page_url, stats, tf_idf_info in pages_with_scores:
            print(f"Page {page_num}")
            print(f"  URL: {page_url}")
            print(f"  Term Frequency (TF): {stats['frequency']}")
            print(f"  Positions: {stats['positions']}")
            
            if tf_idf_info:
                print(f"  IDF: {tf_idf_info.get('idf', 0):.4f}")
                print(f"  TF-IDF Score: {tf_idf_info.get('tf_idf', 0):.4f}")
            print()

    def do_find(self, arg: str) -> None:
        """
        Find pages containing query words, ranked by TF-IDF relevance.
        
        Uses AND logic (all words must appear on same page). Shows spelling
        suggestions if no results found.
        
        Args:
            arg (str): Search query
        
        Output (with results):
            [+] Found 3 pages (ranked by relevance):
            [1] Page 10: https://...
        
        Output (no results):
            [-] No pages found containing all words in: 'frends'
            Did you mean:
              'frends' -> friends, trends
        """
        if not self.is_index_loaded:
            print("[-] Error: An index is not loaded. Please run 'load' first.")
            return

        if not arg:
            print("[-] Error: Please provide a search term.")
            return

        matches: List[str] = self.engine.execute_find(arg)

        if not matches:
            print(f"[-] No pages found containing all words in: '{arg}'")
            
            # Check for spelling errors
            suggestions: Dict[str, List[str]] = self.engine.get_suggestions(arg)
            
            if suggestions:
                print("\nDid you mean:")
                for misspelled, corrections in suggestions.items():
                    print(f"  '{misspelled}' -> {', '.join(corrections)}")
                print()
        else:
            print(f"[+] Found {len(matches)} pages (ranked by relevance):")
            for rank, page_num in enumerate(matches, 1):
                page_url: str = self.manager.page_urls.get(
                    page_num,
                    "Unknown URL"
                )
                print(f"[{rank}] Page {page_num}: {page_url}")

    def do_exit(self, arg: str) -> bool:
        """Exit the application."""
        print("Goodbye!")
        return True

    def do_EOF(self, arg: str) -> bool:
        """Handle EOF (Ctrl+D) to exit gracefully."""
        print()
        return self.do_exit(arg)

    def emptyline(self) -> None:
        """Handle empty line input (pressing Enter with no command)."""
        pass


def main() -> None:
    """
    Application entry point.
    
    Parses command-line arguments and starts the interactive shell.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Quote Search Tool with TF-IDF Ranking"
    )
    args = parser.parse_args()
    
    SearchToolShell().cmdloop()


if __name__ == '__main__':
    main()