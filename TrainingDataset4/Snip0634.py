def search(self, pattern: str) -> bool:
    node = self.root
    for char in pattern:
        if char not in node.children:
            return False
        node = node.children[char]
    return True
