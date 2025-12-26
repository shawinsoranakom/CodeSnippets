def get_height(node: MyNode | None) -> int:
    if node is None:
        return 0
    return node.get_height()
