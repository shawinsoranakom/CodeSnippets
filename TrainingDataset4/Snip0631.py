def __init__(self, text: str) -> None:
    self.text: str = text
    self.root: SuffixTreeNode = SuffixTreeNode()
    self.build_suffix_tree()
