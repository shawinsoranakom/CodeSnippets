def retrace_path(self, node: Node | None) -> list[TPosition]:
    current_node = node
    path = []
    while current_node is not None:
        path.append((current_node.pos_y, current_node.pos_x))
        current_node = current_node.parent
    path.reverse()
    return path
