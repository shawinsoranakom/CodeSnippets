@dataclass
class Node:

    value: int
    left: Node | None = None
    right: Node | None = None

    def __iter__(self) -> Iterator[int]:
        if self.left:
            yield from self.left
        yield self.value
        if self.right:
            yield from self.right

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def mirror(self) -> Node:
        self.left, self.right = self.right, self.left
        if self.left:
            self.left.mirror()
        if self.right:
            self.right.mirror()
        return self
