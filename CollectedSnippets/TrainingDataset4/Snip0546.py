def get(self) -> T:
    if not self.entries:
        raise IndexError("Queue is empty")
    return self.entries.pop(0)
