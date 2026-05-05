# Web Crawler Quote Search Tool

A Python-based web crawler and search engine that scrapes quotes from [quotes.toscrape.com](https://quotes.toscrape.com), builds an inverted index for fast searching, and provides a command-line interface for querying quotes by content or author.

## AI Assistance Declaration
This project was developed with the assistance of Generative AI tools. Generative AI was used to support tasks such as idea generation, drafting text, improving clarity, and refining code or documentation. All final decisions, implementation, and responsibility for the content remain with the project author.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Setup / Installation](#setup--installation)
- [Usage](#usage)
- [Testing](#testing)
- [Dependencies](#dependencies)
- [Project Structure](#project-structure)

---

## Project Overview

This tool demonstrates core information retrieval concepts by implementing:

- **Web Crawler**: Politely scrapes quotes from a website with rate limiting
- **Inverted Index**: Builds a searchable index mapping words to documents
- **Search Engine**: Supports single and multi-word queries with AND logic
- **CLI Interface**: Interactive command-line shell for user interaction

### Key Capabilities

-  Crawl and extract quotes with author attribution
-  Build inverted index with word frequency and position tracking
-  Search for single or multiple words (AND logic)
-  Case-insensitive search with special character handling
-  Persistent storage using JSON format
-  Comprehensive test suite (42 tests)

---

## Setup / Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Internet connection (for initial crawl)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Web_Ser_Crawl.git
   cd Web_Ser_Crawl
   ```

2. **Create virtual environment (recommended)**
   ```bash
   # Using conda
   conda create -n web_dev python=3.13
   conda activate web_dev
   
   # OR using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python -m pytest tests/ -v
   ```

---

## Usage

### Starting the Application

```bash
python -m src.main
```

Or from the src directory:
```bash
cd src
python main.py
```

You'll see:
```
QUOTE SEARCH TOOL - CLI v1.0
Type 'help' to see available commands.
search-tool>
```

### `build` - Crawl and Build Index

**Usage:**
```
search-tool> build
```

**Example Output:**
```
[*] Starting crawl. This will take a few moments due to the required 6-second politeness delay between pages...
[*] Fetching: https://quotes.toscrape.com
    -> Sleeping for 6 seconds to respect server politeness window...
[*] Fetching: https://quotes.toscrape.com/page/2/
    -> Sleeping for 6 seconds to respect server politeness window...
...
[+] Build successful! 100 quotes indexed and saved to:
    /path/to/Web_Ser_Crawl/data/inverted_index.json
```

#### `load` - Load Existing Index

**Usage:**
```
search-tool> load
```

**Example Output:**
```
[+] Loaded 100 quotes from inverted index
[+] Index contains 537 unique terms
[+] Loaded 100 quotes into memory.
```

 
#### `print` - Inspect Index Entry
 
**Usage:**
```
search-tool> print <word>
```
 
**Example Output:**
```
search-tool> print life
 
Inverted Index for: 'life'
Document Frequency: 3 (appears in 3 pages)
 
Page Details:
--------------------------------------------------------------------------------
Page 10
  URL: https://quotes.toscrape.com/page/10/
  Term Frequency (TF): 3
  Positions: [2, 7, 15]
  IDF: 0.6931
  TF-IDF Score: 2.0794
 
Page 5
  URL: https://quotes.toscrape.com/page/5/
  Term Frequency (TF): 1
  Positions: [8]
  IDF: 0.6931
  TF-IDF Score: 0.6931
 
Page 2
  URL: https://quotes.toscrape.com/page/2/
  Term Frequency (TF): 1
  Positions: [3]
  IDF: 0.6931
  TF-IDF Score: 0.6931
```
 
#### `find` - Search for Quotes
 
**Usage:**
```
search-tool> find <query>
```
 
**Example Output:**
```
search-tool> find life
 
[+] Found 15 pages (ranked by relevance):
[1] Page 10: https://quotes.toscrape.com/page/10/
[2] Page 5: https://quotes.toscrape.com/page/5/
[3] Page 2: https://quotes.toscrape.com/page/2/
[4] Page 7: https://quotes.toscrape.com/page/7/
[5] Page 1: https://quotes.toscrape.com/
...
```
 
**Multiple Word Search:**
```
search-tool> find good friends
 
[+] Found 3 pages (ranked by relevance):
[1] Page 10: https://quotes.toscrape.com/page/10/
[2] Page 5: https://quotes.toscrape.com/page/5/
[3] Page 2: https://quotes.toscrape.com/page/2/
```

#### `help` - Show Available Commands

**Usage:**
```
search-tool> help
```

**Example Output:**
```
Documented commands (type help <topic>):
========================================
build  exit  find  help  load  print
```

#### `exit` - Quit Application

**Usage:**
```
search-tool> exit
```

**Example Output:**
```
Goodbye!
```

### Complete Usage Example


```bash
# Start the application
$ python -m src.main
 
QUOTE SEARCH TOOL - CLI v1.0
Type 'help' to see available commands.
 
# First time: build the index
search-tool> build
[*] Starting crawl...
[*] Fetching: https://quotes.toscrape.com
    -> Sleeping for 6 seconds to respect server politeness window...
[*] Fetching: https://quotes.toscrape.com/page/2/
    -> Sleeping for 6 seconds to respect server politeness window...
[+] Build successful! Indexed 100 pages and saved to:
    /path/to/data/inverted_index.json
[+] Note: Only the inverted index is stored, not the full page content.
 
# Search for pages about life
search-tool> find life
[+] Found 15 pages (ranked by relevance):
[1] Page 10: https://quotes.toscrape.com/page/10/
[2] Page 5: https://quotes.toscrape.com/page/5/
[3] Page 2: https://quotes.toscrape.com/page/2/
[4] Page 7: https://quotes.toscrape.com/page/7/
...
 
# Search for multiple words
search-tool> find good friends
[+] Found 3 pages (ranked by relevance):
[1] Page 10: https://quotes.toscrape.com/page/10/
[2] Page 5: https://quotes.toscrape.com/page/5/
[3] Page 2: https://quotes.toscrape.com/page/2/
 
# Inspect a word in the index
search-tool> print life
 
Inverted Index for: 'life'
Document Frequency: 15 (appears in 15 pages)
 
Page Details:
--------------------------------------------------------------------------------
Page 10
  URL: https://quotes.toscrape.com/page/10/
  Term Frequency (TF): 3
  Positions: [2, 7, 15]
  IDF: 0.6931
  TF-IDF Score: 2.0794
 
Page 5
  URL: https://quotes.toscrape.com/page/5/
  Term Frequency (TF): 1
  Positions: [8]
  IDF: 0.6931
  TF-IDF Score: 0.6931
...
 
# Search by author
search-tool> find einstein
[+] Found 3 pages (ranked by relevance):
[1] Page 1: https://quotes.toscrape.com/
[2] Page 4: https://quotes.toscrape.com/page/4/
[3] Page 8: https://quotes.toscrape.com/page/8/
 
# Exit
search-tool> exit
Goodbye!
```
---

## Testing

### Running Tests

**Run all tests (excluding live tests):**
```bash
pytest tests/ -v -m "not live"
```

**Run specific test file:**
```bash
pytest tests/test_indexer.py -v
pytest tests/test_search.py -v
pytest tests/test_crawler.py -v
```

**Run with coverage:**
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

**Include live internet tests:**
```bash
pytest tests/ -v -m live
```

### Test Suite

The project includes **41 comprehensive tests**:

#### test_indexer.py 
- Save and load functionality
- JSON structure validation
- Search integration tests
- Frequency and position tracking
- Edge cases and data integrity

#### test_search.py 
- Single word search
- Multi-word AND search
- Case insensitivity
- Special character handling
- Empty queries

#### test_crawler.py
- HTTP request mocking
- Error handling (timeouts, 404s, 500s)
- Pagination following
- Malformed HTML handling
- 1 live test (requires internet)

### Expected Output

```bash
$ pytest tests/ -v

platform darwin -- Python 3.13.12, pytest-9.0.3
collected 42 items / 1 deselected / 41 selected

tests/test_crawler.py::TestQuoteCrawler::test_crawl_success PASSED         [ 2%]
tests/test_crawler.py::TestQuoteCrawler::test_crawl_network_error PASSED   [ 4%]
...
tests/test_search.py::TestSearchEngine::test_common_word_search PASSED     [100%]

======================== 40 passed, 1 deselected in 2.34s ========================
```

---

## Dependencies

### Core Dependencies (Production)

```
requests          # HTTP library for web scraping
beautifulsoup4    # HTML/XML parsing
lxml              # Fast XML/HTML parser backend
```

### Development Dependencies

```
pytest            # Testing framework
pytest-cov        # Coverage reporting
pytest-mock       # Mocking support
black             # Code formatter
flake8            # Linter
mypy              # Type checker
```

### Installation Options

**Minimal (production only):**
```bash
pip install -r requirements-prod.txt
```

**Standard (recommended):**
```bash
pip install -r requirements.txt
```

**Full development environment:**
```bash
pip install -r requirements-dev.txt
```

## Project Structure

```
Web_Ser_Crawl/
├── .github/ workflows/
│   ├── main.yml          # GitHub Actions Automation
├── src/
│   ├── __init__.py          # Package marker
│   ├── crawler.py           # Web scraper implementation
│   ├── indexer.py           # Index manager and JSON storage
│   ├── search.py            # Search engine with AND logic
│   └── main.py              # CLI interface
├── tests/
│   ├── __init__.py          # Package marker
│   ├── test_crawler.py      # Crawler unit tests
│   ├── test_indexer.py      # Indexer integration tests
│   └── test_search.py       # Search engine unit tests
├── data/
│   └── inverted_index.json  # Generated after first build
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Standard dependencies
└── README.md               # This file
```

---

