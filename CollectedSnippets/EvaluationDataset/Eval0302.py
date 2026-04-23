def merge(left: Node | None, right: Node | None) -> Node | None:
    if (not left) or (not right):
        return left or right
    elif left.prior < right.prior:
        left.right = merge(left.right, right)
        return left
    else:
        right.left = merge(left, right.left)
        return right
