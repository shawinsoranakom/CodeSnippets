def get(self) -> Any:
    if self.is_empty():
        raise IndexError("dequeue from empty queue")
    assert isinstance(self.front, Node)
    node = self.front
    self.front = self.front.next
    if self.front is None:
        self.rear = None
    return node.data
