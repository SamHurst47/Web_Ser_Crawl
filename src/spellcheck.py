"""
Spell checking and query suggestion utilities
Implements Levenshtein distance for "Did You Mean?" functionality
"""

def levenshtein_distance(s1, s2):
    """
    Calculate the Levenshtein distance between two strings.
    
    The Levenshtein distance is the minimum number of single-character edits
    (insertions, deletions, or substitutions) required to change one word into another.
    
    Args:
        s1: First string
        s2: Second string
    
    Returns:
        int: The edit distance between s1 and s2
    
    Examples:
        levenshtein_distance("kitten", "sitting") -> 3
        levenshtein_distance("saturday", "sunday") -> 3
        levenshtein_distance("friends", "frends") -> 1
    """
    # Convert to lowercase for comparison
    s1, s2 = s1.lower(), s2.lower()
    
    # If either string is empty, distance is length of the other
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)
    
    # Create a matrix to store distances
    # Matrix dimensions: (len(s1) + 1) x (len(s2) + 1)
    matrix = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
    
    # Initialize first column (deletions from s1)
    for i in range(len(s1) + 1):
        matrix[i][0] = i
    
    # Initialize first row (insertions to s1)
    for j in range(len(s2) + 1):
        matrix[0][j] = j
    
    # Fill in the rest of the matrix
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            # Cost of substitution (0 if characters match, 1 if they don't)
            cost = 0 if s1[i-1] == s2[j-1] else 1
            
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # Deletion
                matrix[i][j-1] + 1,      # Insertion
                matrix[i-1][j-1] + cost  # Substitution
            )
    
    return matrix[len(s1)][len(s2)]


def suggest_similar_words(word, word_list, max_distance=2, max_suggestions=3):
    """
    Find words similar to the input word using edit distance.
    
    Args:
        word: The word to find suggestions for
        word_list: List of valid words to compare against
        max_distance: Maximum edit distance to consider (default: 2)
        max_suggestions: Maximum number of suggestions to return (default: 3)
    
    Returns:
        list: List of (word, distance) tuples, sorted by distance
    
    Examples:
        suggest_similar_words("frends", ["friends", "trends", "fries"])
        -> [("friends", 1), ("trends", 2)]
    """
    word_lower = word.lower()
    suggestions = []
    
    for candidate in word_list:
        distance = levenshtein_distance(word_lower, candidate)
        
        # Only include words within the max distance
        if distance > 0 and distance <= max_distance:
            suggestions.append((candidate, distance))
    
    # Sort by distance (closest first), then alphabetically
    suggestions.sort(key=lambda x: (x[1], x[0]))
    
    # Return only the top suggestions
    return suggestions[:max_suggestions]


def get_query_suggestions(query_words, index_terms, max_distance=2):
    """
    Get suggestions for misspelled words in a multi-word query.
    
    Args:
        query_words: List of words in the query
        index_terms: Set or list of valid terms in the index
        max_distance: Maximum edit distance for suggestions
    
    Returns:
        dict: Maps misspelled words to their suggestions
              Format: {misspelled_word: [suggestion1, suggestion2, ...]}
    
    Examples:
        get_query_suggestions(["frends", "good"], index_terms)
        -> {"frends": ["friends", "trends"]}
    """
    suggestions_map = {}
    
    for word in query_words:
        word_lower = word.lower()
        
        # If word is not in index, find suggestions
        if word_lower not in index_terms:
            suggestions = suggest_similar_words(word_lower, index_terms, max_distance, max_suggestions=3)
            
            if suggestions:
                # Store just the words, not the distances
                suggestions_map[word] = [sugg for sugg, _ in suggestions]
    
    return suggestions_map