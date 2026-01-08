class Node:
    def __init__(self, data: int) -> None:
        self.data = data
        self.rank: int
        self.parent: Node
