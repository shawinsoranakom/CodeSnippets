@dataclass
class BinaryTree:
    root: Node

    def __iter__(self) -> Iterator[int]:
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def __str__(self) -> str:
        return str(list(self))

    @property
    def is_sum_tree(self) -> bool:
        return self.root.is_sum_node

    @classmethod
    def build_a_tree(cls) -> BinaryTree:
        tree = BinaryTree(Node(11))
        root = tree.root
        root.left = Node(2)
        root.right = Node(29)
        root.left.left = Node(1)
        root.left.right = Node(7)
        root.right.left = Node(15)
        root.right.right = Node(40)
        root.right.right.left = Node(35)
        return tree

    @classmethod
    def build_a_sum_tree(cls) -> BinaryTree:
        tree = BinaryTree(Node(26))
        root = tree.root
        root.left = Node(10)
        root.right = Node(3)
        root.left.left = Node(4)
        root.left.right = Node(6)
        root.right.right = Node(3)
        return tree
