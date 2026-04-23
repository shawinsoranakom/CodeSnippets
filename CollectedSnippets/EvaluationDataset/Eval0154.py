class Token:

    offset: int
    length: int
    indicator: str

    def __repr__(self) -> str:

        return f"({self.offset}, {self.length}, {self.indicator})"
