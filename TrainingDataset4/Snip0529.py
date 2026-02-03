def pop(self) -> Any:
    assert not self.is_empty(), "Deque is empty."
    topop = self._back
    if self._front == self._back:
        self._front = None
        self._back = None
    else:
        self._back = self._back.prev_node
        self._back.next_node = None

    self._len -= 1
    return topop.val
