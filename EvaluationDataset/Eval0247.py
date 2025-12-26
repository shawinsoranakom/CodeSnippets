class BinaryTreeNode:

    def __init__(self, data: int) -> None:
        self.data = data
        self.left_child: BinaryTreeNode | None = None
        self.right_child: BinaryTreeNode | None = None
