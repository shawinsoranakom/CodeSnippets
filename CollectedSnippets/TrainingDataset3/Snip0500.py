class Node:
    data: Any
    next_node: Node | None = None

    def __repr__(self) -> str:
        return f"Node({self.data})"
