def push(self, data: T) -> None:
    if self.head is None:
        self.head = Node(data)
    else:
        new_node = Node(data)
        self.head.prev = new_node
        new_node.next = self.head
        new_node.prev = None
        self.head = new_node
