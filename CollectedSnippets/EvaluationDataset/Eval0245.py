@dataclass
class Node:
    key: int
    left: Node | None = None
    right: Node | None = None

    def __iter__(self) -> Iterator[int]:
        if self.left:
            yield from self.left
        yield self.key
        if self.right:
            yield from self.right

    def __len__(self) -> int:
        return sum(1 for _ in self)
