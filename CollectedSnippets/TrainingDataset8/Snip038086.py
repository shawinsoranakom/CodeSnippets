def __iter__(self) -> Iterator[str]:
        return iter(self.__nested_secrets__)