class SkewHeap[T: bool]:
    def __init__(self, data: Iterable[T] | None = ()) -> None:
        self._root: SkewNode[T] | None = None
        if data:
            for item in data:
                self.insert(item)

    def __bool__(self) -> bool:
        return self._root is not None

    def __iter__(self) -> Iterator[T]:
        result: list[Any] = []
        while self:
            result.append(self.pop())

        for item in result:
            self.insert(item)

        return iter(result)

    def insert(self, value: T) -> None:
        self._root = SkewNode.merge(self._root, SkewNode(value))

    def pop(self) -> T | None:
        result = self.top()
        self._root = (
            SkewNode.merge(self._root.left, self._root.right) if self._root else None
        )

        return result

    def top(self) -> T:
        if not self._root:
            raise IndexError("Can't get top element for the empty heap.")
        return self._root.value

    def clear(self) -> None:
        self._root = None
