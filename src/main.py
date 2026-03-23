import cmd
import os
from crawler import QuoteCrawler

class SearchToolShell(cmd.Cmd):
    intro = 'Quote Indexer Shell. Type "build" to start or "exit" to quit.\n'
    prompt = 'search-tool> '
    
    def do_build(self, arg):
        """Builds the index and saves it to ../data/index.txt"""
        print("Starting crawl...")
        
        # 1. Perform the crawl
        crawler = QuoteCrawler()
        results = crawler.crawl()
        
        if not results:
            print("Error: No data retrieved.")
            return

        # 2. Define path: One directory back (..) then into 'data' folder
        target_dir = os.path.join(os.getcwd(), "..", "data")
        file_path = os.path.join(target_dir, "index.txt")

        try:
            # Create the 'data' directory if it doesn't exist
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                print(f"[*] Created directory: {target_dir}")

            # 3. Save the index
            with open(file_path, "w", encoding="utf-8") as f:
                for item in results:
                    f.write(f"AUTHOR: {item['author']}\nQUOTE: {item['text']}\n{'-'*20}\n")
            
            print(f"[+] Build successful! Index saved to: {os.path.abspath(file_path)}")
            print(f"[+] Total quotes indexed: {len(results)}")
            
        except Exception as e:
            print(f"[-] Critical Error: {e}")

    def do_exit(self, arg):
        """Exit the shell."""
        print("Closing...")
        return True

    def do_EOF(self, arg):
        return True

if __name__ == '__main__':
    SearchToolShell().cmdloop()