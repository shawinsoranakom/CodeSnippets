def insert(self, word: str) -> None:
    curr = self
    for char in word:
        if char not in curr.nodes:
            curr.nodes[char] = TrieNode()
        curr = curr.nodes[char]
    curr.is_leaf = True
