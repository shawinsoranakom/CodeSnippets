def __repr__(self) -> str:
    return f"Queue({tuple(self._stack2[::-1] + self._stack1)})"
