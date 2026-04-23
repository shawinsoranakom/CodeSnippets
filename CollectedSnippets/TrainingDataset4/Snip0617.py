def __iter__(self) -> Iterator[T]:
    node = self.top
    while node:
        yield node.data
        node = node.next
