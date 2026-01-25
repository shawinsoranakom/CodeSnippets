class CircularLinkedList:
    head: Node | None = None 
    tail: Node | None = None 

    def __iter__(self) -> Iterator[Any]:
        node = self.head
        while node:
            yield node.data
            node = node.next_node
            if node == self.head:
                break

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __repr__(self) -> str:
        return "->".join(str(item) for item in iter(self))

    def insert_tail(self, data: Any) -> None:
        self.insert_nth(len(self), data)

    def insert_head(self, data: Any) -> None:
        self.insert_nth(0, data)

    def insert_nth(self, index: int, data: Any) -> None:
        if index < 0 or index > len(self):
            raise IndexError("list index out of range.")
        new_node: Node = Node(data)
        if self.head is None:
            new_node.next_node = new_node 
            self.tail = self.head = new_node
        elif index == 0:
            new_node.next_node = self.head
            assert self.tail is not None  
            self.head = self.tail.next_node = new_node
        else:
            temp: Node | None = self.head
            for _ in range(index - 1):
                assert temp is not None
                temp = temp.next_node
            assert temp is not None
            new_node.next_node = temp.next_node
            temp.next_node = new_node
            if index == len(self) - 1: 
                self.tail = new_node

    def delete_front(self) -> Any:
        return self.delete_nth(0)

    def delete_tail(self) -> Any:
        return self.delete_nth(len(self) - 1)

    def delete_nth(self, index: int = 0) -> Any:
        if not 0 <= index < len(self):
            raise IndexError("list index out of range.")

        assert self.head is not None
        assert self.tail is not None
        delete_node: Node = self.head
        if self.head == self.tail: 
            self.head = self.tail = None
        elif index == 0:
            assert self.tail.next_node is not None
            self.tail.next_node = self.tail.next_node.next_node
            self.head = self.head.next_node
        else:
            temp: Node | None = self.head
            for _ in range(index - 1):
                assert temp is not None
                temp = temp.next_node
            assert temp is not None
            assert temp.next_node is not None
            delete_node = temp.next_node
            temp.next_node = temp.next_node.next_node
            if index == len(self) - 1: 
                self.tail = temp
        return delete_node.data

    def is_empty(self) -> bool:
        return len(self) == 0
