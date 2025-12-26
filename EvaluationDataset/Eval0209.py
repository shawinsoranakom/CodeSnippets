@dataclass
class BinarySearchTree:
    root: Node | None = None

    def __bool__(self) -> bool:
        return bool(self.root)

    def __iter__(self) -> Iterator[int]:
        yield from self.root or []

    def __str__(self) -> str:
        return str(self.root)

    def __reassign_nodes(self, node: Node, new_children: Node | None) -> None:
        if new_children is not None: 
            new_children.parent = node.parent
        if node.parent is not None:  
            if node.is_right: 
                node.parent.right = new_children
            else:
                node.parent.left = new_children
        else:
            self.root = new_children

    def empty(self) -> bool:
        return not self.root

    def __insert(self, value) -> None:
        new_node = Node(value) 
        if self.empty(): 
            self.root = new_node  
        else: 
            parent_node = self.root
            if parent_node is None:
                return
            while True: 
                if value < parent_node.value:  
                    if parent_node.left is None:
                        parent_node.left = new_node 
                        break
                    else:
                        parent_node = parent_node.left
                elif parent_node.right is None:
                    parent_node.right = new_node
                    break
                else:
                    parent_node = parent_node.right
            new_node.parent = parent_node

    def insert(self, *values) -> Self:
        for value in values:
            self.__insert(value)
        return self

    def search(self, value) -> Node | None:
        if self.empty():
            raise IndexError("Warning: Tree is empty! please use another.")
        else:
            node = self.root
            while node is not None and node.value is not value:
                node = node.left if value < node.value else node.right
            return node

    def get_max(self, node: Node | None = None) -> Node | None:
        if node is None:
            if self.root is None:
                return None
            node = self.root

        if not self.empty():
            while node.right is not None:
                node = node.right
        return node

    def get_min(self, node: Node | None = None) -> Node | None:
        if node is None:
            node = self.root
        if self.root is None:
            return None
        if not self.empty():
            node = self.root
            while node.left is not None:
                node = node.left
        return node

    def remove(self, value: int) -> None:
        node = self.search(value)
        if node is None:
            msg = f"Value {value} not found"
            raise ValueError(msg)

        if node.left is None and node.right is None: 
            self.__reassign_nodes(node, None)
        elif node.left is None: 
            self.__reassign_nodes(node, node.right)
        elif node.right is None: 
            self.__reassign_nodes(node, node.left)
        else:
            predecessor = self.get_max(
                node.left
            )  
            self.remove(predecessor.value)  
            node.value = (
                predecessor.value  
            )  

    def preorder_traverse(self, node: Node | None) -> Iterable:
        if node is not None:
            yield node 
            yield from self.preorder_traverse(node.left)
            yield from self.preorder_traverse(node.right)

    def traversal_tree(self, traversal_function=None) -> Any:
        if traversal_function is None:
            return self.preorder_traverse(self.root)
        else:
            return traversal_function(self.root)

    def inorder(self, arr: list, node: Node | None) -> None:
        if node:
            self.inorder(arr, node.left)
            arr.append(node.value)
            self.inorder(arr, node.right)

    def find_kth_smallest(self, k: int, node: Node) -> int:
        arr: list[int] = []
        self.inorder(arr, node) 
        return arr[k - 1]

