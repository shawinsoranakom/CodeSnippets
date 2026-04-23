class Heap:

    def __init__(self, key: Callable | None = None) -> None:
        self.arr: list = []
        self.pos_map: dict = {}
        self.size = 0
        self.key = key or (lambda x: x)

    def _parent(self, i: int) -> int | None:
        return int((i - 1) / 2) if i > 0 else None

    def _left(self, i: int) -> int | None:
        left = int(2 * i + 1)
        return left if 0 < left < self.size else None

    def _right(self, i: int) -> int | None:
        right = int(2 * i + 2)
        return right if 0 < right < self.size else None

    def _swap(self, i: int, j: int) -> None:
        self.pos_map[self.arr[i][0]], self.pos_map[self.arr[j][0]] = (
            self.pos_map[self.arr[j][0]],
            self.pos_map[self.arr[i][0]],
        )
        self.arr[i], self.arr[j] = self.arr[j], self.arr[i]

    def _cmp(self, i: int, j: int) -> bool:
        return self.arr[i][1] < self.arr[j][1]

    def _get_valid_parent(self, i: int) -> int:
        left = self._left(i)
        right = self._right(i)
        valid_parent = i

        if left is not None and not self._cmp(left, valid_parent):
            valid_parent = left
        if right is not None and not self._cmp(right, valid_parent):
            valid_parent = right

        return valid_parent

    def _heapify_up(self, index: int) -> None:
        parent = self._parent(index)
        while parent is not None and not self._cmp(index, parent):
            self._swap(index, parent)
            index, parent = parent, self._parent(parent)

    def _heapify_down(self, index: int) -> None:
        valid_parent = self._get_valid_parent(index)
        while valid_parent != index:
            self._swap(index, valid_parent)
            index, valid_parent = valid_parent, self._get_valid_parent(valid_parent)

    def update_item(self, item: int, item_value: int) -> None:
        if item not in self.pos_map:
            return
        index = self.pos_map[item]
        self.arr[index] = [item, self.key(item_value)]
        self._heapify_up(index)
        self._heapify_down(index)

    def delete_item(self, item: int) -> None:
        if item not in self.pos_map:
            return
        index = self.pos_map[item]
        del self.pos_map[item]
        self.arr[index] = self.arr[self.size - 1]
        self.pos_map[self.arr[self.size - 1][0]] = index
        self.size -= 1
        if self.size > index:
            self._heapify_up(index)
            self._heapify_down(index)

    def insert_item(self, item: int, item_value: int) -> None:
        arr_len = len(self.arr)
        if arr_len == self.size:
            self.arr.append([item, self.key(item_value)])
        else:
            self.arr[self.size] = [item, self.key(item_value)]
        self.pos_map[item] = self.size
        self.size += 1
        self._heapify_up(self.size - 1)

    def get_top(self) -> tuple | None:
        return self.arr[0] if self.size else None

    def extract_top(self) -> tuple | None:
      
        top_item_tuple = self.get_top()
        if top_item_tuple:
            self.delete_item(top_item_tuple[0])
        return top_item_tuple
