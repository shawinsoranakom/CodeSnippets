def erase(root: Node | None, value: int) -> Node | None:
    left, right = split(root, value - 1)
    _, right = split(right, value)
    return merge(left, right)
