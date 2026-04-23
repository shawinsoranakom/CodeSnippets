def __init__(self, iterable: Iterable[T] | None = None) -> None:
    self._stack1: list[T] = list(iterable or [])
    self._stack2: list[T] = []
