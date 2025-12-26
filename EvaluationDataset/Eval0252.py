@dataclass
class Node:
    data: float
    left: Node | None = None
    right: Node | None = None

    def __iter__(self) -> Iterator[float]:
        if self.left:
            yield from self.left
        yield self.data
        if self.right:
            yield from self.right

    @property
    def is_sorted(self) -> bool:
        if self.left and (self.data < self.left.data or not self.left.is_sorted):
            return False
        return not (
            self.right and (self.data > self.right.data or not self.right.is_sorted)
        )

