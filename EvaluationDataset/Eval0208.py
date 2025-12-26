@dataclass
class Node:
    value: int
    left: Node | None = None
    right: Node | None = None
    parent: Node | None = None  

    def __iter__(self) -> Iterator[int]:
        yield from self.left or []
        yield self.value
        yield from self.right or []

    def __repr__(self) -> str:
        from pprint import pformat

        if self.left is None and self.right is None:
            return str(self.value)
        return pformat({f"{self.value}": (self.left, self.right)}, indent=1)

    @property
    def is_right(self) -> bool:
        return bool(self.parent and self is self.parent.right)

