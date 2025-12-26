def preorder(root: Node | None) -> Generator[int]:
    if not root:
        return
    yield root.data
    yield from preorder(root.left)
    yield from preorder(root.right)
