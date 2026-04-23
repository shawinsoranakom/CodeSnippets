def print_words(node: TrieNode, word: str) -> None:
    if node.is_leaf:
        print(word, end=" ")

    for key, value in node.nodes.items():
        print_words(value, word + key)
