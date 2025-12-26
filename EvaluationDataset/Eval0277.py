def color(node: RedBlackTree | None) -> int:
    if node is None:
        return 0
    else:
        return node.color
