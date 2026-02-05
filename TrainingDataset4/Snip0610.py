def pop(self) -> T | None:
    if self.head is None:
        return None
    else:
        assert self.head is not None
        temp = self.head.data
        self.head = self.head.next
        if self.head is not None:
            self.head.prev = None
        return temp
