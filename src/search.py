import re
from spellcheck import get_query_suggestions

class SearchEngine:
    def __init__(self, index_manager):
        self.manager = index_manager

    def execute_find(self, query):
        """
        Find pages containing the query words using TF-IDF ranking.
        Returns page IDs ranked by relevance (sum of TF-IDF scores).
        """
        # Clean the query and split into individual words
        query_words = re.findall(r'\w+', query.lower())
        
        if not query_words:
            return []

        # Get all pages containing ALL query words (AND logic)
        if query_words[0] in self.manager.inverted_index:
            result_set = set(self.manager.inverted_index[query_words[0]].keys())
        else:
            return []

        # Intersect with pages containing all other query words
        for word in query_words[1:]:
            if word in self.manager.inverted_index:
                word_set = set(self.manager.inverted_index[word].keys())
                result_set = result_set.intersection(word_set)
            else:
                # If any word is not in the index, no results
                return []
            
            # Optimization: If the intersection is already empty, stop
            if not result_set:
                break

        if not result_set:
            return []

        # Calculate relevance score for each page
        # Score = sum of TF-IDF scores for all query terms
        scored_results = []
        
        for page_id in result_set:
            score = 0.0
            
            # Sum TF-IDF scores for all query words in this page
            for word in query_words:
                if word in self.manager.tf_idf_scores:
                    if page_id in self.manager.tf_idf_scores[word]:
                        score += self.manager.tf_idf_scores[word][page_id]["tf_idf"]
            
            scored_results.append({
                "page_id": page_id,
                "score": score
            })
        
        # Sort by score (descending - highest relevance first)
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Return just the page IDs in ranked order
        return [result["page_id"] for result in scored_results]
    
    def get_suggestions(self, query):
        """
        Get spelling suggestions for query words not in the index.
        
        Args:
            query: The search query string
        
        Returns:
            dict: Maps misspelled words to suggestions
                  Format: {misspelled_word: [suggestion1, suggestion2, ...]}
        """
        query_words = re.findall(r'\w+', query.lower())
        
        if not query_words:
            return {}
        
        # Get all terms in the index
        index_terms = set(self.manager.inverted_index.keys())
        
        # Get suggestions for words not in index
        return get_query_suggestions(query_words, index_terms, max_distance=2)