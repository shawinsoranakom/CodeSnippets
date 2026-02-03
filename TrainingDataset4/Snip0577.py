def push(self, data: T) -> None:
    if len(self.stack) >= self.limit:
        raise StackOverflowError
    self.stack.append(data)
