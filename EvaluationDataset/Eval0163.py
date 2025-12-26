@dataclass
class Index2DArrayIterator:
    matrix: list[list[int]]

    def __iter__(self) -> Iterator[int]:

        for row in self.matrix:
            yield from row
