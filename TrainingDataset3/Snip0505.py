class Node[KT, VT]:
    def __init__(self, key: KT | str = "root", value: VT | None = None):
        self.key = key
        self.value = value
        self.forward: list[Node[KT, VT]] = []

    def __repr__(self) -> str:

        return f"Node({self.key}: {self.value})"

    @property
    def level(self) -> int:

        return len(self.forward)

