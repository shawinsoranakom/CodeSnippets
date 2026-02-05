def push(self, item: T) -> None:
    node = Node(item)
    if not self.is_empty():
        node.next = self.top
    self.top = node
