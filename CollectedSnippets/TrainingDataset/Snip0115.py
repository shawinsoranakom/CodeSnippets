def backtrack(
    current_word: str, path: list[str], end_word: str, word_set: set[str]
) -> list[str]:

    if current_word == end_word:
        return path

    for i in range(len(current_word)):
        for c in string.ascii_lowercase:  
            transformed_word = current_word[:i] + c + current_word[i + 1 :]
            if transformed_word in word_set:
                word_set.remove(transformed_word)
                result = backtrack(
                    transformed_word, [*path, transformed_word], end_word, word_set
                )
                if result:  
                    return result
                word_set.add(transformed_word)  

    return []  
