def put(self, item: Any) -> None:
    node = Node(item)
    if self.is_empty():
        self.front = self.rear = node
    else:
        assert isinstance(self.rear, Node)
        self.rear.next = node
        self.rear = node
