def put(self, item: Any) -> None:
    self.stack.append(item)
    self.length = self.length + 1
