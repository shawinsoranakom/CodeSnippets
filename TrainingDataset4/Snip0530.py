def popleft(self) -> Any:
    assert not self.is_empty(), "Deque is empty."

    topop = self._front
    if self._front == self._back:
        self._front = None
        self._back = None
    else:
        self._front = self._front.next_node  
        self._front.prev_node = None

    self._len -= 1

    return topop.val
