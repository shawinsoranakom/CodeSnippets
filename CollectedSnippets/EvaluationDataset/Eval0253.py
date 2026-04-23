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

    @property
    def is_sum_node(self) -> bool:
        if not self.left and not self.right:
            return True  
        left_sum = sum(self.left) if self.left else 0
        right_sum = sum(self.right) if self.right else 0
        return all(
            (
                self.data == left_sum + right_sum,
                self.left.is_sum_node if self.left else True,
                self.right.is_sum_node if self.right else True,
            )
        )

