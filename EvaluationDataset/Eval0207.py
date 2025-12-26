@dataclass
class BinaryTree:
    root: Node

    def __iter__(self) -> Iterator[int]:
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    @classmethod
    def small_tree(cls) -> BinaryTree:
        binary_tree = BinaryTree(Node(2))
        binary_tree.root.left = Node(1)
        binary_tree.root.right = Node(3)
        return binary_tree

    @classmethod
    def medium_tree(cls) -> BinaryTree:
        binary_tree = BinaryTree(Node(4))
        binary_tree.root.left = two = Node(2)
        two.left = Node(1)
        two.right = Node(3)
        binary_tree.root.right = five = Node(5)
        five.right = six = Node(6)
        six.right = Node(7)
        return binary_tree

    def depth(self) -> int:

        return self._depth(self.root)

    def _depth(self, node: Node | None) -> int:
        if not node:
            return 0
        return 1 + max(self._depth(node.left), self._depth(node.right))

    def is_full(self) -> bool:
        return self.root.is_full()
