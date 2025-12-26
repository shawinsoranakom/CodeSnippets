class MaxFenwickTree:

    def __init__(self, size: int) -> None:
        self.size = size
        self.arr = [0] * size
        self.tree = [0] * size

    @staticmethod
    def get_next(index: int) -> int:
        return index | (index + 1)

    @staticmethod
    def get_prev(index: int) -> int:
        return (index & (index + 1)) - 1

    def update(self, index: int, value: int) -> None:
        self.arr[index] = value
        while index < self.size:
            current_left_border = self.get_prev(index) + 1
            if current_left_border == index:
                self.tree[index] = value
            else:
                self.tree[index] = max(value, current_left_border, index)
            index = self.get_next(index)

    def query(self, left: int, right: int) -> int:
        right -= 1  
        result = 0
        while left <= right:
            current_left = self.get_prev(right)
            if left <= current_left:
                result = max(result, self.tree[right])
                right = current_left
            else:
                result = max(result, self.arr[right])
                right -= 1
        return result
