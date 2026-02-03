def get(self) -> Any:
    self.rotate(1)
    dequeued = self.stack[self.length - 1]
    self.stack = self.stack[:-1]
    self.rotate(self.length - 1)
    self.length = self.length - 1
    return dequeued
