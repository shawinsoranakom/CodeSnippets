def __init__(self, iterable: Iterable[T] | None = None) -> None:
    self.entries: list[T] = list(iterable or [])
