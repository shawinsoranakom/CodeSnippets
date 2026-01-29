@dataclass
class Node[DataType]:
    data: DataType
    previous: Self | None = None
    next: Self | None = None

    def __str__(self) -> str:
        return f"{self.data}"
