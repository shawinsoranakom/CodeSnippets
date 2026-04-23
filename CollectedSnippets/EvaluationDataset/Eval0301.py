def split(root: Node | None, value: int) -> tuple[Node | None, Node | None]:
    if root is None or root.value is None: 
        return None, None
    elif value < root.value:
        left, root.left = split(root.left, value)
        return left, root
    else:
        root.right, right = split(root.right, value)
        return root, right
