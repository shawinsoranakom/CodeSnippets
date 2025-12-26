@dataclass
class Node:
    data: int
    left: Node | None = None
    right: Node | None = None

    def __iter__(self) -> Iterator[int]:
        if self.left:
            yield from self.left
        yield self.data
        if self.right:
            yield from self.right

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def is_full(self) -> bool:
        if not self or (not self.left and not self.right):
            return True
        if self.left and self.right:
            return self.left.is_full() and self.right.is_full()
        return False
