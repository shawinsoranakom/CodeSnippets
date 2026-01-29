@dataclass
class LinkedList:
    head: Node | None = None
    tail: Node | None = None 

    def __str__(self):
        current = self.head
        nodes = []
        while current is not None:
            nodes.append(current.data)
            current = current.next
        return " ".join(str(node) for node in nodes)

    def __contains__(self, value: DataType):
        current = self.head
        while current:
            if current.data == value:
                return True
            current = current.next
        return False

    def __iter__(self):
        return LinkedListIterator(self.head)

    def get_head_data(self):
        if self.head:
            return self.head.data
        return None

    def get_tail_data(self):
        if self.tail:
            return self.tail.data
        return None

    def set_head(self, node: Node) -> None:
        if self.head is None:
            self.head = node
            self.tail = node
        else:
            self.insert_before_node(self.head, node)

    def set_tail(self, node: Node) -> None:
        if self.tail is None:
            self.head = node
            self.tail = node
        else:
            self.insert_after_node(self.tail, node)

    def insert(self, value: DataType) -> None:
        node = Node(value)
        if self.head is None:
            self.set_head(node)
        else:
            self.set_tail(node)

    def insert_before_node(self, node: Node, node_to_insert: Node) -> None:
        node_to_insert.next = node
        node_to_insert.previous = node.previous

        if node.previous is None:
            self.head = node_to_insert
        else:
            node.previous.next = node_to_insert

        node.previous = node_to_insert

    def insert_after_node(self, node: Node, node_to_insert: Node) -> None:
        node_to_insert.previous = node
        node_to_insert.next = node.next

        if node.next is None:
            self.tail = node_to_insert
        else:
            node.next.previous = node_to_insert

        node.next = node_to_insert

    def insert_at_position(self, position: int, value: DataType) -> None:
        current_position = 1
        new_node = Node(value)
        node = self.head
        while node:
            if current_position == position:
                self.insert_before_node(node, new_node)
                return
            current_position += 1
            node = node.next
        self.set_tail(new_node)

    def get_node(self, item: DataType) -> Node:
        node = self.head
        while node:
            if node.data == item:
                return node
            node = node.next
        raise Exception("Node not found")

    def delete_value(self, value):
        if (node := self.get_node(value)) is not None:
            if node == self.head:
                self.head = self.head.next

            if node == self.tail:
                self.tail = self.tail.previous

            self.remove_node_pointers(node)

    @staticmethod
    def remove_node_pointers(node: Node) -> None:
        if node.next:
            node.next.previous = node.previous

        if node.previous:
            node.previous.next = node.next

        node.next = None
        node.previous = None

    def is_empty(self):
        return self.head is None
