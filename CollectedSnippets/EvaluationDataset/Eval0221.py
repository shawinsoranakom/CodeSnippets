class BinaryTreePathSum:

    target: int

    def __init__(self) -> None:
        self.paths = 0

    def depth_first_search(self, node: Node | None, path_sum: int) -> None:
        if node is None:
            return

        if path_sum == self.target:
            self.paths += 1

        if node.left:
            self.depth_first_search(node.left, path_sum + node.left.value)
        if node.right:
            self.depth_first_search(node.right, path_sum + node.right.value)

    def path_sum(self, node: Node | None, target: int | None = None) -> int:
        if node is None:
            return 0
        if target is not None:
            self.target = target

        self.depth_first_search(node, node.value)
        self.path_sum(node.left)
        self.path_sum(node.right)

        return self.paths
