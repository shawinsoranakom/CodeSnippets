def get(self) -> T:
    stack1_pop = self._stack1.pop
    stack2_append = self._stack2.append

    if not self._stack2:
        while self._stack1:
            stack2_append(stack1_pop())

    if not self._stack2:
        raise IndexError("Queue is empty")
    return self._stack2.pop()
