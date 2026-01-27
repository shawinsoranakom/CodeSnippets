class BinaryHeap:

    def __init__(self):
        self.__heap = [0]
        self.__size = 0

    def __swap_up(self, i: int) -> None:
        """Swap the element up"""
        temporary = self.__heap[i]
        while i // 2 > 0:
            if self.__heap[i] > self.__heap[i // 2]:
                self.__heap[i] = self.__heap[i // 2]
                self.__heap[i // 2] = temporary
            i //= 2

    def insert(self, value: int) -> None:
        """Insert new element"""
        self.__heap.append(value)
        self.__size += 1
        self.__swap_up(self.__size)

    def __swap_down(self, i: int) -> None:
        """Swap the element down"""
        while self.__size >= 2 * i:
            if 2 * i + 1 > self.__size:
                bigger_child = 2 * i
            elif self.__heap[2 * i] > self.__heap[2 * i + 1]:
                bigger_child = 2 * i
            else:
                bigger_child = 2 * i + 1
            temporary = self.__heap[i]
            if self.__heap[i] < self.__heap[bigger_child]:
                self.__heap[i] = self.__heap[bigger_child]
                self.__heap[bigger_child] = temporary
            i = bigger_child

    def pop(self) -> int:
        max_value = self.__heap[1]
        self.__heap[1] = self.__heap[self.__size]
        self.__size -= 1
        self.__heap.pop()
        self.__swap_down(1)
        return max_value

    @property
    def get_list(self):
        return self.__heap[1:]

    def __len__(self):
        return self.__size
