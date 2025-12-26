def insert(root: Node | None, value: int) -> Node | None:
    node = Node(value)
    left, right = split(root, value)
    return merge(merge(left, node), right)
