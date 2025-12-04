def word_ladder(begin_word: str, end_word: str, word_set: set[str]) -> list[str]:
    if end_word not in word_set:  
        return []

    return backtrack(begin_word, [begin_word], end_word, word_set)
