def pop(self) -> T:
    if not self.stack:
        raise StackUnderflowError
    return self.stack.pop()
