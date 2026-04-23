def delete_nth(self, index: int = 0) -> Any:
        """
        Delete and return the data of the node at the nth pos in Circular Linked List.
        Args:
            index (int): The index of the node to be deleted. Defaults to 0.
        Returns:
            Any: The data of the deleted node.
        Raises:
            IndexError: If the index is out of range.
        """
        if not 0 <= index < len(self):
            raise IndexError("list index out of range.")

        assert self.head is not None
        assert self.tail is not None
        delete_node: Node = self.head
        if self.head == self.tail:  # Just one node
            self.head = self.tail = None
        elif index == 0:  # Delete head node
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
            if index == len(self) - 1:  # Delete at tail
                self.tail = temp
        return delete_node.data