class Heap[T: Comparable]:

    def __init__(self) -> None:
        self.h: list[T] = []
        self.heap_size: int = 0

    def __repr__(self) -> str:
        return str(self.h)

    def parent_index(self, child_idx: int) -> int | None:
        if child_idx > 0:
            return (child_idx - 1) // 2
        return None

    def left_child_idx(self, parent_idx: int) -> int | None:
        left_child_index = 2 * parent_idx + 1
        if left_child_index < self.heap_size:
            return left_child_index
        return None

    def right_child_idx(self, parent_idx: int) -> int | None:
        right_child_index = 2 * parent_idx + 2
        if right_child_index < self.heap_size:
            return right_child_index
        return None

    def max_heapify(self, index: int) -> None:
        
        if index < self.heap_size:
            violation: int = index
            left_child = self.left_child_idx(index)
            right_child = self.right_child_idx(index)
            if left_child is not None and self.h[left_child] > self.h[violation]:
                violation = left_child
            if right_child is not None and self.h[right_child] > self.h[violation]:
                violation = right_child
            if violation != index:
                self.h[violation], self.h[index] = self.h[index], self.h[violation]
                self.max_heapify(violation)

    def build_max_heap(self, collection: Iterable[T]) -> None:
        self.h = list(collection)
        self.heap_size = len(self.h)
        if self.heap_size > 1:
            for i in range(self.heap_size // 2 - 1, -1, -1):
                self.max_heapify(i)

    def extract_max(self) -> T:
        if self.heap_size >= 2:
            me = self.h[0]
            self.h[0] = self.h.pop(-1)
            self.heap_size -= 1
            self.max_heapify(0)
            return me
        elif self.heap_size == 1:
            self.heap_size -= 1
            return self.h.pop(-1)
        else:
            raise Exception("Empty heap")

    def insert(self, value: T) -> None:
        self.h.append(value)
        idx = (self.heap_size - 1) // 2
        self.heap_size += 1
        while idx >= 0:
            self.max_heapify(idx)
            idx = (idx - 1) // 2

    def heap_sort(self) -> None:
        size = self.heap_size
        for j in range(size - 1, 0, -1):
            self.h[0], self.h[j] = self.h[j], self.h[0]
            self.heap_size -= 1
            self.max_heapify(0)
        self.heap_size = size


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    for unsorted in [
        [0],
        [2],
        [3, 5],
        [5, 3],
        [5, 5],
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [2, 2, 3, 5],
        [0, 2, 2, 3, 5],
        [2, 5, 3, 0, 2, 3, 0, 3],
        [6, 1, 2, 7, 9, 3, 4, 5, 10, 8],
        [103, 9, 1, 7, 11, 15, 25, 201, 209, 107, 5],
        [-45, -2, -5],
    ]:
        print(f"unsorted array: {unsorted}")

        heap: Heap[int] = Heap()
        heap.build_max_heap(unsorted)
        print(f"after build heap: {heap}")

        print(f"max value: {heap.extract_max()}")
        print(f"after max value removed: {heap}")

        heap.insert(100)
        print(f"after new value 100 inserted: {heap}")

        heap.heap_sort()
        print(f"heap-sorted array: {heap}\n")
