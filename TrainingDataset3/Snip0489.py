class SortedLinkedList:
    def __init__(self, ints: Iterable[int]) -> None:
        self.head: Node | None = None
        for i in sorted(ints, reverse=True):
            self.head = Node(i, self.head)

    def __iter__(self) -> Iterator[int]:
        
        node = self.head
        while node:
            yield node.data
            node = node.next_node

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __str__(self) -> str:
        return " -> ".join([str(node) for node in self])


def merge_lists(
    sll_one: SortedLinkedList, sll_two: SortedLinkedList
) -> SortedLinkedList:
    return SortedLinkedList(list(sll_one) + list(sll_two))
