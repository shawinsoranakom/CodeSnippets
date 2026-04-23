class MyQueue:
    def __init__(self) -> None:
        self.data: list[Any] = []
        self.head: int = 0
        self.tail: int = 0

    def is_empty(self) -> bool:
        return self.head == self.tail

    def push(self, data: Any) -> None:
        self.data.append(data)
        self.tail = self.tail + 1

    def pop(self) -> Any:
        ret = self.data[self.head]
        self.head = self.head + 1
        return ret

    def count(self) -> int:
        return self.tail - self.head

    def print_queue(self) -> None:
        print(self.data)
        print("**************")
        print(self.data[self.head : self.tail])
