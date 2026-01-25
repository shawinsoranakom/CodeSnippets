class Node:
    def __init__(self, length: int) -> None:
        self.minn: int = -1
        self.maxx: int = -1
        self.map_left: list[int] = [-1] * length
        self.left: Node | None = None
        self.right: Node | None = None

    def __repr__(self) -> str:
        return f"Node(min_value={self.minn} max_value={self.maxx})"
