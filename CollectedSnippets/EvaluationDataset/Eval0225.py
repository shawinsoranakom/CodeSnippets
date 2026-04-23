def inorder(root: Node | None) -> Generator[int]:
    if not root:
        return
    yield from inorder(root.left)
    yield root.data
    yield from inorder(root.right)
