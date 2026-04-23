class LinkedList:

    def __init__(self) -> None:
        self.head: Node | None = None
        self.tail: Node | None = None  

    def __iter__(self) -> Iterator[int]:
        node = self.head
        while node:
            yield node.data
            node = node.next_node

    def __repr__(self) -> str:
        return " -> ".join([str(data) for data in self])

    def append(self, data: int) -> None:
        if self.tail:
            self.tail.next_node = self.tail = Node(data)
        else:
            self.head = self.tail = Node(data)

    def extend(self, items: Iterable[int]) -> None:
        for item in items:
            self.append(item)


def make_linked_list(elements_list: Iterable[int]) -> LinkedList:
    if not elements_list:
        raise Exception("The Elements List is empty")

    linked_list = LinkedList()
    linked_list.extend(elements_list)
    return linked_list
