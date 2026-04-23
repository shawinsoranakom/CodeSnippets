def reverse_k_nodes(self, group_size: int) -> None:
        """
        reverse nodes within groups of size k
        >>> ll = LinkedList([1, 2, 3, 4, 5])
        >>> ll.reverse_k_nodes(2)
        >>> tuple(ll)
        (2, 1, 4, 3, 5)
        >>> str(ll)
        '2 -> 1 -> 4 -> 3 -> 5'
        """
        if self.head is None or self.head.next_node is None:
            return

        length = len(self)
        dummy_head = Node(0)
        dummy_head.next_node = self.head
        previous_node = dummy_head

        while length >= group_size:
            current_node = previous_node.next_node
            assert current_node
            next_node = current_node.next_node
            for _ in range(1, group_size):
                assert next_node, current_node
                current_node.next_node = next_node.next_node
                assert previous_node
                next_node.next_node = previous_node.next_node
                previous_node.next_node = next_node
                next_node = current_node.next_node
            previous_node = current_node
            length -= group_size
        self.head = dummy_head.next_node