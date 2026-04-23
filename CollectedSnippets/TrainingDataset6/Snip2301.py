def __iter__(self) -> Generator[str, None, None]:
        for item in self.data:
            if self.open:
                yield item
            else:
                raise ValueError("Session closed")