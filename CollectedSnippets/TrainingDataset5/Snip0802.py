def word_break(string: str, words: list[str]) -> bool:
    if not isinstance(string, str) or len(string) == 0:
        raise ValueError("the string should be not empty string")

    if not isinstance(words, list) or not all(
        isinstance(item, str) and len(item) > 0 for item in words
    ):
        raise ValueError("the words should be a list of non-empty strings")

    trie: dict[str, Any] = {}
    word_keeper_key = "WORD_KEEPER"

    for word in words:
        trie_node = trie
        for c in word:
            if c not in trie_node:
                trie_node[c] = {}

            trie_node = trie_node[c]

        trie_node[word_keeper_key] = True

    len_string = len(string)

    @functools.cache
    def is_breakable(index: int) -> bool:
        if index == len_string:
            return True

        trie_node: Any = trie
        for i in range(index, len_string):
            trie_node = trie_node.get(string[i], None)

            if trie_node is None:
                return False

            if trie_node.get(word_keeper_key, False) and is_breakable(i + 1):
                return True

        return False

    return is_breakable(0)
