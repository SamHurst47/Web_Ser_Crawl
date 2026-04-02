import re

class SearchEngine:
    def __init__(self, index_manager):
        self.manager = index_manager

    def execute_find(self, query):
        """
        Processes a query string (e.g., 'good friends') and returns 
        IDs of quotes containing ALL those words.
        """
        # Tokenize the query into individual words
        query_words = re.findall(r'\w+', query.lower())
        if not query_words:
            return []

        # Get the set of IDs for the first word
        # We access the inverted_index from the manager
        results = self.manager.inverted_index.get(query_words[0], set())

        # Perform Intersection (AND logic) for subsequent words
        for word in query_words[1:]:
            word_ids = self.manager.inverted_index.get(word, set())
            results = results.intersection(word_ids)
            
            if not results: # Optimization: stop if no common IDs remain
                break
                
        return sorted(list(results))