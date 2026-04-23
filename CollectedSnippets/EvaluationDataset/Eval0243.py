def flatten(root: TreeNode | None) -> None:
    if not root:
        return

    flatten(root.left)

    right_subtree = root.right

    root.right = root.left
    root.left = None

    current = root
    while current.right:
        current = current.right

    current.right = right_subtree

    flatten(right_subtree)
