def pop(self) -> T:
    if self.is_empty():
        raise IndexError("pop from empty stack")
    assert isinstance(self.top, Node)
    pop_node = self.top
    self.top = self.top.next
    return pop_node.data
