def reverse_inorder(root: Node | None) -> Generator[int]:
    if not root:
        return
    yield from reverse_inorder(root.right)
    yield root.data
    yield from reverse_inorder(root.left)
