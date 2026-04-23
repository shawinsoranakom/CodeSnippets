def appendleft(self, val: Any) -> None:
    node = self._Node(val, None, None)
    if self.is_empty():
        self._front = self._back = node
        self._len = 1
    else:
        node.next_node = self._front
        self._front.prev_node = node
        self._front = node 
        self._len += 1
        assert not self.is_empty(), "Error on appending value."
