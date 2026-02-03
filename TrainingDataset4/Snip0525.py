def __init__(self, iterable: Iterable[Any] | None = None) -> None:
    self._front: Any = None
    self._back: Any = None
    self._len: int = 0
    if iterable is not None:
        for val in iterable:
            self.append(val)
