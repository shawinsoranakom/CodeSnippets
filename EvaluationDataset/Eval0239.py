def distribute_coins(root: TreeNode | None) -> int:

    if root is None:
        return 0

    def count_nodes(node: TreeNode | None) -> int:
        """
        >>> count_nodes(None)
        0
        """
        if node is None:
            return 0

        return count_nodes(node.left) + count_nodes(node.right) + 1
