import random
import string
import time
from collections import Counter


def analyze_text(text):
    """
    Analyzes the given text and returns various statistics including word frequencies,
    unique word count, and character statistics.
    """
    # Remove punctuation and convert text to lowercase
    clean_text = text.translate(str.maketrans('', '', string.punctuation)).lower()

    words = clean_text.split()

    # Word frequencies
    word_count = Counter(words)

    # Unique words
    unique_words = set(words)

    # Character count
    char_count = sum(len(word) for word in words)

    # Sentence count
    sentence_count = text.count('.') + text.count('!') + text.count('?')

    return {
        "word_count": len(words),
        "unique_words": len(unique_words),
        "char_count": char_count,
        "sentence_count": sentence_count,
        "top_words": word_count.most_common(10)
    }


def summation(number1, number2):
    a = number1+ number2
    return a
