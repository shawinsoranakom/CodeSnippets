class FenwickTree:

    def __init__(self, arr: list[int] | None = None, size: int | None = None) -> None:

        if arr is None and size is not None:
            self.size = size
            self.tree = [0] * size
        elif arr is not None:
            self.init(arr)
        else:
            raise ValueError("Either arr or size must be specified")

    def init(self, arr: list[int]) -> None:
        
        self.size = len(arr)
        self.tree = deepcopy(arr)
        for i in range(1, self.size):
            j = self.next_(i)
            if j < self.size:
                self.tree[j] += self.tree[i]

    def get_array(self) -> list[int]:
        arr = self.tree[:]
        for i in range(self.size - 1, 0, -1):
            j = self.next_(i)
            if j < self.size:
                arr[j] -= arr[i]
        return arr

    @staticmethod
    def next_(index: int) -> int:
        return index + (index & (-index))

    @staticmethod
    def prev(index: int) -> int:
        return index - (index & (-index))

    def add(self, index: int, value: int) -> None:
        if index == 0:
            self.tree[0] += value
            return
        while index < self.size:
            self.tree[index] += value
            index = self.next_(index)

    def update(self, index: int, value: int) -> None:
        self.add(index, value - self.get(index))

    def prefix(self, right: int) -> int:
        if right == 0:
            return 0
        result = self.tree[0]
        right -= 1 
        while right > 0:
            result += self.tree[right]
            right = self.prev(right)
        return result

    def query(self, left: int, right: int) -> int:
        return self.prefix(right) - self.prefix(left)

    def get(self, index: int) -> int:
        return self.query(index, index + 1)

    def rank_query(self, value: int) -> int:
        value -= self.tree[0]
        if value < 0:
            return -1

        j = 1 
        while j * 2 < self.size:
            j *= 2

        i = 0

        while j > 0:
            if i + j < self.size and self.tree[i + j] <= value:
                value -= self.tree[i + j]
                i += j
            j //= 2
        return i
