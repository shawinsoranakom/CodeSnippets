def insert_nth(self, index: int, data: Any) -> None:
        """
        Insert the data of the node at the nth pos in the Circular Linked List.
        Args:
            index: The index at which the data should be inserted.
            data: The data to be inserted.

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index > len(self):
            raise IndexError("list index out of range.")
        new_node: Node = Node(data)
        if self.head is None:
            new_node.next_node = new_node  # First node points to itself
            self.tail = self.head = new_node
        elif index == 0:  # Insert at the head
            new_node.next_node = self.head
            assert self.tail is not None  # List is not empty, tail exists
            self.head = self.tail.next_node = new_node
        else:
            temp: Node | None = self.head
            for _ in range(index - 1):
                assert temp is not None
                temp = temp.next_node
            assert temp is not None
            new_node.next_node = temp.next_node
            temp.next_node = new_node
            if index == len(self) - 1:  # Insert at the tail
                self.tail = new_node