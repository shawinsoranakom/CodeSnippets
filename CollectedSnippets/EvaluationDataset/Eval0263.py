class Node:
    def __init__(self, value: int = 0) -> None:
        self.value = value
        self.left: Node | None = None
        self.right: Node | None = None
