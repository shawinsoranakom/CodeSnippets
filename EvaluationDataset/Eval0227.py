def height(root: Node | None) -> int:
    return (max(height(root.left), height(root.right)) + 1) if root else 0
