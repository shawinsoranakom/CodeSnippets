@dataclass
class Node:
    data: int
    left: Node | None = None
    right: Node | None = None

    def depth(self) -> int:
        left_depth = self.left.depth() if self.left else 0
        right_depth = self.right.depth() if self.right else 0
        return max(left_depth, right_depth) + 1

    def diameter(self) -> int:
        left_depth = self.left.depth() if self.left else 0
        right_depth = self.right.depth() if self.right else 0
        return left_depth + right_depth + 1

