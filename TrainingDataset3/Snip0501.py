class LinkedList:
    def __init__(self):
        self.head = None

    def __iter__(self) -> Iterator[Any]:
        node = self.head
        while node:
            yield node.data
            node = node.next_node

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __repr__(self) -> str:
        return " -> ".join([str(item) for item in self])

    def __getitem__(self, index: int) -> Any:
        if not 0 <= index < len(self):
            raise ValueError("list index out of range.")
        for i, node in enumerate(self):
            if i == index:
                return node
        return None

    def __setitem__(self, index: int, data: Any) -> None:
        if not 0 <= index < len(self):
            raise ValueError("list index out of range.")
        current = self.head
        for _ in range(index):
            current = current.next_node
        current.data = data

    def insert_tail(self, data: Any) -> None:
        self.insert_nth(len(self), data)

    def insert_head(self, data: Any) -> None:
        self.insert_nth(0, data)

    def insert_nth(self, index: int, data: Any) -> None:
        if not 0 <= index <= len(self):
            raise IndexError("list index out of range")
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
        elif index == 0:
            new_node.next_node = self.head 
            self.head = new_node
        else:
            temp = self.head
            for _ in range(index - 1):
                temp = temp.next_node
            new_node.next_node = temp.next_node
            temp.next_node = new_node

    def print_list(self) -> None:
        print(self)

    def delete_head(self) -> Any:
        return self.delete_nth(0)

    def delete_tail(self) -> Any: 
        return self.delete_nth(len(self) - 1)

    def delete_nth(self, index: int = 0) -> Any:
        if not 0 <= index <= len(self) - 1:  
            raise IndexError("List index out of range.")
        delete_node = self.head 
        if index == 0:
            self.head = self.head.next_node
        else:
            temp = self.head
            for _ in range(index - 1):
                temp = temp.next_node
            delete_node = temp.next_node
            temp.next_node = temp.next_node.next_node
        return delete_node.data

    def is_empty(self) -> bool:
        return self.head is None

    def reverse(self) -> None:
        prev = None
        current = self.head

        while current:
            next_node = current.next_node
            current.next_node = prev
            prev = current
            current = next_node
        self.head = prev

