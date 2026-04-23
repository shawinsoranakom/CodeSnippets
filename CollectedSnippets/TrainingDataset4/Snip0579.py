def peek(self) -> T:
    if not self.stack:
        raise StackUnderflowError
    return self.stack[-1]
