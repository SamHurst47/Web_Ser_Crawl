"""
spellcheck.py - Spell checking and query suggestion utilities.

This module implements Levenshtein distance for "Did You Mean?" functionality.
Provides spell checking to suggest corrections for misspelled search queries.

Example:
    >>> from spellcheck import levenshtein_distance, suggest_similar_words
    >>> distance = levenshtein_distance("frends", "friends")  # Returns 1
    >>> word_list = ["friends", "trends", "fries"]
    >>> suggestions = suggest_similar_words("frends", word_list)
    >>> # Returns [("friends", 1), ("trends", 2)]
"""

from typing import List, Tuple, Dict, Set


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.
    
    The Levenshtein distance is the minimum number of single-character edits
    (insertions, deletions, or substitutions) required to transform one word
    into another. Uses dynamic programming with O(m*n) time complexity.
    
    Args:
        s1 (str): First string to compare
        s2 (str): Second string to compare
    
    Returns:
        int: The minimum edit distance between s1 and s2
    
    Examples:
        >>> levenshtein_distance("kitten", "sitting")
        3
        >>> levenshtein_distance("friends", "frends")
        1
    
    Note:
        Comparison is case-insensitive.
    """
    # Convert to lowercase for case-insensitive comparison
    s1, s2 = s1.lower(), s2.lower()
    
    # Base cases: if either string is empty, distance is length of the other
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)
    
    # Create distance matrix
    matrix = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
    
    # Initialize first column (deletions from s1)
    for i in range(len(s1) + 1):
        matrix[i][0] = i
    
    # Initialize first row (insertions to s1)
    for j in range(len(s2) + 1):
        matrix[0][j] = j
    
    # Fill matrix using dynamic programming
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # Deletion
                matrix[i][j-1] + 1,      # Insertion
                matrix[i-1][j-1] + cost  # Substitution
            )
    
    return matrix[len(s1)][len(s2)]


def suggest_similar_words(
    word: str,
    word_list: List[str],
    max_distance: int = 2,
    max_suggestions: int = 3
) -> List[Tuple[str, int]]:
    """
    Find words similar to the input word using Levenshtein edit distance.
    
    Args:
        word (str): The word to find suggestions for
        word_list (List[str]): List of valid words to compare against
        max_distance (int, optional): Maximum edit distance to consider. Default is 2.
        max_suggestions (int, optional): Maximum suggestions to return. Default is 3.
    
    Returns:
        List[Tuple[str, int]]: List of (word, distance) tuples sorted by distance.
            Empty list if no suggestions found within max_distance.
    
    Examples:
        >>> word_list = ["friends", "trends", "fries"]
        >>> suggest_similar_words("frends", word_list)
        [("friends", 1), ("trends", 2)]
    
    Note:
        The input word itself (distance 0) is excluded from suggestions.
    """
    word_lower = word.lower()
    suggestions: List[Tuple[str, int]] = []
    
    # Calculate distance for each candidate word
    for candidate in word_list:
        distance = levenshtein_distance(word_lower, candidate)
        
        # Only include words within max distance, excluding exact matches
        if distance > 0 and distance <= max_distance:
            suggestions.append((candidate, distance))
    
    # Sort by distance (closest first), then alphabetically
    suggestions.sort(key=lambda x: (x[1], x[0]))
    
    return suggestions[:max_suggestions]


def get_query_suggestions(
    query_words: List[str],
    index_terms: Set[str],
    max_distance: int = 2
) -> Dict[str, List[str]]:
    """
    Get spelling suggestions for misspelled words in a multi-word query.
    
    Args:
        query_words (List[str]): List of words from the search query
        index_terms (Set[str]): Set of valid terms in the search index
        max_distance (int, optional): Maximum edit distance. Default is 2.
    
    Returns:
        Dict[str, List[str]]: Maps misspelled words to suggestions.
            Format: {misspelled_word: [suggestion1, suggestion2, ...]}
            Empty dict if all words are in the index.
    
    Examples:
        >>> index_terms = {"friends", "good", "life"}
        >>> get_query_suggestions(["frends", "good"], index_terms)
        {"frends": ["friends"]}
    """
    suggestions_map: Dict[str, List[str]] = {}
    
    for word in query_words:
        word_lower = word.lower()
        
        # If word not in index, find suggestions
        if word_lower not in index_terms:
            suggestions = suggest_similar_words(
                word_lower,
                list(index_terms),
                max_distance,
                max_suggestions=3
            )
            
            if suggestions:
                # Store just the words, not the distances
                suggestions_map[word] = [sugg for sugg, _ in suggestions]
    
    return suggestions_map