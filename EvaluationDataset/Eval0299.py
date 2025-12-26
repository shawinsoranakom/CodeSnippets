def is_mirror(left: Node | None, right: Node | None) -> bool:
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    if left.data == right.data:
        return is_mirror(left.left, right.right) and is_mirror(left.right, right.left)
    return False
