class Comparable(Protocol):
    @abstractmethod
    def __lt__(self: T, other: T) -> bool:
        pass

    @abstractmethod
    def __gt__(self: T, other: T) -> bool:
        pass

    @abstractmethod
    def __eq__(self: T, other: object) -> bool:
        pass
