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
        # Extract doc_ids from the inverted index structure: {"word": {"doc_id": {...}}}
        if query_words[0] in self.manager.inverted_index:
            result_set = set(self.manager.inverted_index[query_words[0]].keys())
        else:
            return []

        # 3. Intersect with sets of all subsequent words
        for word in query_words[1:]:
            if word in self.manager.inverted_index:
                word_set = set(self.manager.inverted_index[word].keys())
                result_set = result_set.intersection(word_set)
            else:
                # If any word is not in the index, no results
                return []
            
            # Optimization: If the intersection is already empty, stop looking
            if not result_set:
                break

        # Return a sorted list of IDs (convert string IDs to integers for proper sorting)
        return sorted(list(result_set), key=lambda x: int(x))