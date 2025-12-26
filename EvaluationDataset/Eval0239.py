def distribute_coins(root: TreeNode | None) -> int:

    if root is None:
        return 0

    def count_nodes(node: TreeNode | None) -> int:
        if node is None:
            return 0

        return count_nodes(node.left) + count_nodes(node.right) + 1

    def count_coins(node: TreeNode | None) -> int:
        if node is None:
            return 0

        return count_coins(node.left) + count_coins(node.right) + node.data

    if count_nodes(root) != count_coins(root):
        raise ValueError("The nodes number should be same as the number of coins")

    def get_distrib(node: TreeNode | None) -> CoinsDistribResult:

        if node is None:
            return CoinsDistribResult(0, 1)

        left_distrib_moves, left_distrib_excess = get_distrib(node.left)
        right_distrib_moves, right_distrib_excess = get_distrib(node.right)

        coins_to_left = 1 - left_distrib_excess
        coins_to_right = 1 - right_distrib_excess

        result_moves = (
            left_distrib_moves
            + right_distrib_moves
            + abs(coins_to_left)
            + abs(coins_to_right)
        )
        result_excess = node.data - coins_to_left - coins_to_right

        return CoinsDistribResult(result_moves, result_excess)

    return get_distrib(root)[0]
