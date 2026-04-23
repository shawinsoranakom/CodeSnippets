def postorder(root: Node | None) -> Generator[int]:
    if not root:
        return
    yield from postorder(root.left)
    yield from postorder(root.right)
    yield root.data
