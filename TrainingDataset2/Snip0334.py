class RandomizedHeap[T: bool]:
    def __init__(self, data: Iterable[T] | None = ()) -> None:
        self._root: RandomizedHeapNode[T] | None = None

        if data:
            for item in data:
                self.insert(item)

    def insert(self, value: T) -> None:
        self._root = RandomizedHeapNode.merge(self._root, RandomizedHeapNode(value))

    def pop(self) -> T | None:
        result = self.top()

        if self._root is None:
            return None

        self._root = RandomizedHeapNode.merge(self._root.left, self._root.right)

        return result

    def top(self) -> T:
        if not self._root:
            raise IndexError("Can't get top element for the empty heap.")
        return self._root.value

    def clear(self) -> None:
        self._root = None

    def to_sorted_list(self) -> list[Any]:
        result = []
        while self:
            result.append(self.pop())

        return result

    def __bool__(self) -> bool:
        return self._root is not None
