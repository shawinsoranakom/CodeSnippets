def peek(self) -> T:
    if self.is_empty():
        raise IndexError("peek from empty stack")

    assert self.top is not None
    return self.top.data
