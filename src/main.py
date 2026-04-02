import cmd
import os
import argparse
import sys
from crawler import QuoteCrawler
from indexer import IndexManager
from search import SearchEngine

class SearchToolShell(cmd.Cmd):
    intro = "QUOTE SEARCH TOOL - CLI v1.0 /n Type 'help' to see available commands."
    prompt = 'search-tool> '
    
    def __init__(self):
        super().__init__()
        self.manager = IndexManager()
        self.engine = SearchEngine(self.manager)

    # --- HELP DOCUMENTATION ---

    def help_build(self):
        print("\nUsage: build")
        print("Description: Crawls the website, indexes quotes, and saves to ../data/index.txt\n")

    def help_load(self):
        print("\nUsage: load")
        print("Description: Loads the saved index from the file system into memory.\n")

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
        """Build the index from the web."""
        print("[*] Building index...")
        crawler = QuoteCrawler()
        results = crawler.crawl()
        
        if not results:
            print("[-] Error: No data found.")
            return

        target_dir = os.path.join(os.getcwd(), "..", "data")
        file_path = os.path.join(target_dir, "index.txt")

        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            with open(file_path, "w", encoding="utf-8") as f:
                for item in results:
                    f.write(f"AUTHOR: {item['author']}\nQUOTE: {item['text']}\n{'-'*20}\n")
            print(f"[+] Build successful! Saved to {file_path}")
        except Exception as e:
            print(f"[-] File error: {e}")

    def do_load(self, arg):
        """Load index from file."""
        data = self.manager.load_index()
        if data:
            print(f"[+] Loaded {len(data)} quotes.")
        else:
            print("[-] Load failed. Does ../data/index.txt exist?")

    def do_print(self, arg):
        """Print inverted index for a word."""
        if not arg:
            self.help_print()
            return
        word = arg.strip().lower()
        ids = self.manager.inverted_index.get(word, [])
        print(f"Word: '{word}' -> IDs: {list(ids)}")

    def do_find(self, arg):
        """Find phrase in index."""
        if not arg:
            self.help_find()
            return
        matches = self.engine.execute_find(arg)
        if not matches:
            print("[-] No matches found.")
        else:
            for idx in matches:
                print(f"\n[ID {idx}]\n{self.manager.quotes[idx]}")

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