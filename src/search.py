import re

class SearchEngine:
    def __init__(self, index_manager):
        self.manager = index_manager

    def execute_find(self, query):
        # 1. Clean the query and split into individual words
        # This handles "good friends" -> ["good", "friends"]
        query_words = re.findall(r'\w+', query.lower())
        
        if not query_words:
            return []

        # 2. Get the starting set from the first word
        # We use .get(word, set()) to avoid KeyErrors if the word isn't indexed
        result_set = self.manager.inverted_index.get(query_words[0], set())

        # 3. Intersect with sets of all subsequent words
        for word in query_words[1:]:
            word_set = self.manager.inverted_index.get(word, set())
            result_set = result_set.intersection(word_set)
            
            # Optimization: If the intersection is already empty, stop looking
            if not result_set:
                break

        # Return a sorted list of IDs
        return sorted(list(result_set))