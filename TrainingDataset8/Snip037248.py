def __str__(self) -> str:
        return f"'{self.name}': {self.path if self.path is not None else self.url}"