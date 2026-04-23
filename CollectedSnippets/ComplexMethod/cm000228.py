def swap_nodes(self, node_data_1: Any, node_data_2: Any) -> None:
        """
        Swap the positions of two nodes in the Linked List based on their data values.

        Args:
            node_data_1: Data value of the first node to be swapped.
            node_data_2: Data value of the second node to be swapped.


        Note:
            If either of the specified data values isn't found then, no swapping occurs.

        Examples:
        When both values are present in a linked list.
            >>> linked_list = LinkedList()
            >>> linked_list.push(5)
            >>> linked_list.push(4)
            >>> linked_list.push(3)
            >>> linked_list.push(2)
            >>> linked_list.push(1)
            >>> list(linked_list)
            [1, 2, 3, 4, 5]
            >>> linked_list.swap_nodes(1, 5)
            >>> tuple(linked_list)
            (5, 2, 3, 4, 1)

        When one value is present and the other isn't in the linked list.
            >>> second_list = LinkedList()
            >>> second_list.push(6)
            >>> second_list.push(7)
            >>> second_list.push(8)
            >>> second_list.push(9)
            >>> second_list.swap_nodes(1, 6) is None
            True

        When both values are absent in the linked list.
            >>> second_list = LinkedList()
            >>> second_list.push(10)
            >>> second_list.push(9)
            >>> second_list.push(8)
            >>> second_list.push(7)
            >>> second_list.swap_nodes(1, 3) is None
            True

        When linkedlist is empty.
            >>> second_list = LinkedList()
            >>> second_list.swap_nodes(1, 3) is None
            True

        Returns:
            None
        """
        if node_data_1 == node_data_2:
            return

        node_1 = self.head
        while node_1 and node_1.data != node_data_1:
            node_1 = node_1.next_node
        node_2 = self.head
        while node_2 and node_2.data != node_data_2:
            node_2 = node_2.next_node
        if node_1 is None or node_2 is None:
            return
        # Swap the data values of the two nodes
        node_1.data, node_2.data = node_2.data, node_1.data