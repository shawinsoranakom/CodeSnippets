class LinkedList:
    def __init__(self, ints: Iterable[int]) -> None:
        self.head: Node | None = None
        for i in ints:
            self.append(i)

    def __iter__(self) -> Iterator[int]:
        node = self.head
        while node:
            yield node.data
            node = node.next_node

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __str__(self) -> str:
        return " -> ".join([str(node) for node in self])

    def append(self, data: int) -> None:
        if not self.head:
            self.head = Node(data)
            return
        node = self.head
        while node.next_node:
            node = node.next_node
        node.next_node = Node(data)

    def reverse_k_nodes(self, group_size: int) -> None:
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
