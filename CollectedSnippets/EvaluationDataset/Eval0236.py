def binary_tree_left_side_view(root: TreeNode) -> list[int]:

    def depth_first_search(
        root: TreeNode | None, depth: int, left_view: list[int]
    ) -> None:
        if not root:
            return

        if depth == len(left_view):
            left_view.append(root.val)

        depth_first_search(root.left, depth + 1, left_view)
        depth_first_search(root.right, depth + 1, left_view)

    left_view: list = []
    if not root:
        return left_view

    depth_first_search(root, 0, left_view)
    return left_view
