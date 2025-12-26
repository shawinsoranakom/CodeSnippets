def binary_tree_right_side_view(root: TreeNode) -> list[int]:

    def depth_first_search(
        root: TreeNode | None, depth: int, right_view: list[int]
    ) -> None:
        if not root:
            return

        if depth == len(right_view):
            right_view.append(root.val)

        depth_first_search(root.right, depth + 1, right_view)
        depth_first_search(root.left, depth + 1, right_view)

    right_view: list = []
    if not root:
        return right_view

    depth_first_search(root, 0, right_view)
    return right_view
