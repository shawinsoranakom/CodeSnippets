def __iter__(self) -> Iterator[Any]:
    node = self.front
    while node:
        yield node.data
        node = node.next
