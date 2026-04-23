def append(self, val: Any) -> None:
    node = self._Node(val, None, None)
    if self.is_empty():
        self._front = self._back = node
        self._len = 1
    else:
        self._back.next_node = node
        node.prev_node = self._back
        self._back = node 
        self._len += 1
        assert not self.is_empty(), "Error on appending value."
