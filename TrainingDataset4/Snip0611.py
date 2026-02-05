def top(self) -> T | None:
    return self.head.data if self.head is not None else None
