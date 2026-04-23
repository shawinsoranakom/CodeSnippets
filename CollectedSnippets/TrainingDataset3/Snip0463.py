class SkewNode[T: bool]:

    def __init__(self, value: T) -> None:
        self._value: T = value
        self.left: SkewNode[T] | None = None
        self.right: SkewNode[T] | None = None

    @property
    def value(self) -> T:
        return self._value

    @staticmethod
    def merge(
        root1: SkewNode[T] | None, root2: SkewNode[T] | None
    ) -> SkewNode[T] | None:
        if not root1:
            return root2

        if not root2:
            return root1

        if root1.value > root2.value:
            root1, root2 = root2, root1

        result = root1
        temp = root1.right
        result.right = root1.left
        result.left = SkewNode.merge(temp, root2)

        return result


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
