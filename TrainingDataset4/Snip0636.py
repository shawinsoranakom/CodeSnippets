def __init__(self, prefix: str = "", is_leaf: bool = False) -> None:
    self.nodes: dict[str, RadixNode] = {}

    self.is_leaf = is_leaf

    self.prefix = prefix
