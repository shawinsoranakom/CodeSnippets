def find(self, word: str) -> bool:
    curr = self
    for char in word:
        if char not in curr.nodes:
            return False
        curr = curr.nodes[char]
    return curr.is_leaf
