def get_nodes_from_left_to_right(root: Node | None, level: int) -> Generator[int]:

    def populate_output(root: Node | None, level: int) -> Generator[int]:
        if not root:
            return
        if level == 1:
            yield root.data
        elif level > 1:
            yield from populate_output(root.left, level - 1)
            yield from populate_output(root.right, level - 1)

    yield from populate_output(root, level)
