def min_distance_up_bottom(word1: str, word2: str) -> int:
    len_word1 = len(word1)
    len_word2 = len(word2)

    @functools.cache
    def min_distance(index1: int, index2: int) -> int:
        if index1 >= len_word1:
            return len_word2 - index2
        if index2 >= len_word2:
            return len_word1 - index1
        diff = int(word1[index1] != word2[index2]) 
        return min(
            1 + min_distance(index1 + 1, index2),
            1 + min_distance(index1, index2 + 1),
            diff + min_distance(index1 + 1, index2 + 1),
        )

    return min_distance(0, 0)
