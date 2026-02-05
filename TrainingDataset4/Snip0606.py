def peek(self) -> int | None:
    return self.main_queue[0] if self.main_queue else None
