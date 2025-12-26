class TreeNode:

    def __init__(self, data: int) -> None:
        self.data = data
        self.left: TreeNode | None = None
        self.right: TreeNode | None = None
