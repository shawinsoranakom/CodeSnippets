class SegmentTree[T]:
    def __init__(self, arr: list[T], fnc: Callable[[T, T], T]) -> None:
        any_type: Any | T = None

        self.N: int = len(arr)
        self.st: list[T] = [any_type for _ in range(self.N)] + arr
        self.fn = fnc
        self.build()

    def build(self) -> None:
        for p in range(self.N - 1, 0, -1):
            self.st[p] = self.fn(self.st[p * 2], self.st[p * 2 + 1])

    def update(self, p: int, v: T) -> None:
        p += self.N
        self.st[p] = v
        while p > 1:
            p = p // 2
            self.st[p] = self.fn(self.st[p * 2], self.st[p * 2 + 1])

    def query(self, left: int, right: int) -> T | None:
        left, right = left + self.N, right + self.N

        res: T | None = None
        while left <= right:
            if left % 2 == 1:
                res = self.st[left] if res is None else self.fn(res, self.st[left])
            if right % 2 == 0:
                res = self.st[right] if res is None else self.fn(res, self.st[right])
            left, right = (left + 1) // 2, (right - 1) // 2
        return res
