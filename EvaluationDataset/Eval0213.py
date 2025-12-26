class BinarySearchTree:
    def __init__(self) -> None:
        self.root: Node | None = None

    def empty(self) -> None:

        self.root = None

    def is_empty(self) -> bool:

        return self.root is None

    def put(self, label: int) -> None:

        self.root = self._put(self.root, label)

    def _put(self, node: Node | None, label: int, parent: Node | None = None) -> Node:
        if node is None:
            node = Node(label, parent)
        elif label < node.label:
            node.left = self._put(node.left, label, node)
        elif label > node.label:
            node.right = self._put(node.right, label, node)
        else:
            msg = f"Node with label {label} already exists"
            raise ValueError(msg)

        return node

    def search(self, label: int) -> Node:

        return self._search(self.root, label)

    def _search(self, node: Node | None, label: int) -> Node:
        if node is None:
            msg = f"Node with label {label} does not exist"
            raise ValueError(msg)
        elif label < node.label:
            node = self._search(node.left, label)
        elif label > node.label:
            node = self._search(node.right, label)

        return node

    def remove(self, label: int) -> None:

        node = self.search(label)
        if node.right and node.left:
            lowest_node = self._get_lowest_node(node.right)
            lowest_node.left = node.left
            lowest_node.right = node.right
            node.left.parent = lowest_node
            if node.right:
                node.right.parent = lowest_node
            self._reassign_nodes(node, lowest_node)
        elif not node.right and node.left:
            self._reassign_nodes(node, node.left)
        elif node.right and not node.left:
            self._reassign_nodes(node, node.right)
        else:
            self._reassign_nodes(node, None)

    def _reassign_nodes(self, node: Node, new_children: Node | None) -> None:
        if new_children:
            new_children.parent = node.parent

        if node.parent:
            if node.parent.right == node:
                node.parent.right = new_children
            else:
                node.parent.left = new_children
        else:
            self.root = new_children

    def _get_lowest_node(self, node: Node) -> Node:
        if node.left:
            lowest_node = self._get_lowest_node(node.left)
        else:
            lowest_node = node
            self._reassign_nodes(node, node.right)

        return lowest_node

    def exists(self, label: int) -> bool:

        try:
            self.search(label)
            return True
        except ValueError:
            return False

    def get_max_label(self) -> int:

        if self.root is None:
            raise ValueError("Binary search tree is empty")

        node = self.root
        while node.right is not None:
            node = node.right

        return node.label

    def get_min_label(self) -> int:

        if self.root is None:
            raise ValueError("Binary search tree is empty")

        node = self.root
        while node.left is not None:
            node = node.left

        return node.label

    def inorder_traversal(self) -> Iterator[Node]:

        return self._inorder_traversal(self.root)

    def _inorder_traversal(self, node: Node | None) -> Iterator[Node]:
        if node is not None:
            yield from self._inorder_traversal(node.left)
            yield node
            yield from self._inorder_traversal(node.right)

    def preorder_traversal(self) -> Iterator[Node]:
        return self._preorder_traversal(self.root)

    def _preorder_traversal(self, node: Node | None) -> Iterator[Node]:
        if node is not None:
            yield node
            yield from self._preorder_traversal(node.left)
            yield from self._preorder_traversal(node.right)
