def max_sum_bst(root: TreeNode | None) -> int:
    ans: int = 0

    def solver(node: TreeNode | None) -> tuple[bool, int, int, int]:
        nonlocal ans

        if not node:
            return True, INT_MAX, INT_MIN, 0 

        is_left_valid, min_left, max_left, sum_left = solver(node.left)
        is_right_valid, min_right, max_right, sum_right = solver(node.right)

        if is_left_valid and is_right_valid and max_left < node.val < min_right:
            total_sum = sum_left + sum_right + node.val
            ans = max(ans, total_sum)
            return True, min(min_left, node.val), max(max_right, node.val), total_sum

        return False, -1, -1, -1  

    solver(root)
    return ans
