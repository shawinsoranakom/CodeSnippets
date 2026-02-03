def front(self) -> Any:
    front = self.get()
    self.put(front)
    self.rotate(self.length - 1)
    return front
