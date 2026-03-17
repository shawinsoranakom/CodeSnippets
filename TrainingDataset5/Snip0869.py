def get_successors(self, parent: Node) -> list[Node]:
    successors = []
    for action in delta:
        pos_x = parent.pos_x + action[1]
        pos_y = parent.pos_y + action[0]
        if not (0 <= pos_x <= len(grid[0]) - 1 and 0 <= pos_y <= len(grid) - 1):
            continue

        if grid[pos_y][pos_x] != 0:
            continue

        successors.append(
            Node(
                pos_x,
                pos_y,
                self.target.pos_y,
                self.target.pos_x,
                parent.g_cost + 1,
                parent,
            )
        )
    return successors
