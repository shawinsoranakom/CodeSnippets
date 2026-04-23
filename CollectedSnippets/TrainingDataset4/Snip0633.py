def _add_suffix(self, suffix: str, index: int) -> None:
    node = self.root
    for char in suffix:
        if char not in node.children:
            node.children[char] = SuffixTreeNode()
        node = node.children[char]
    node.is_end_of_string = True
    node.start = index
    node.end = index + len(suffix) - 1
