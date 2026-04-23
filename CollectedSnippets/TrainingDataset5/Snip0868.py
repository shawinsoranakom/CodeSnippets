def search(self) -> list[TPosition]:
    while self.open_nodes:
        self.open_nodes.sort()
        current_node = self.open_nodes.pop(0)

        if current_node.pos == self.target.pos:
            return self.retrace_path(current_node)

        self.closed_nodes.append(current_node)
        successors = self.get_successors(current_node)

        for child_node in successors:
            if child_node in self.closed_nodes:
                continue

            if child_node not in self.open_nodes:
                self.open_nodes.append(child_node)
            else:
                better_node = self.open_nodes.pop(self.open_nodes.index(child_node))

                if child_node.g_cost < better_node.g_cost:
                    self.open_nodes.append(child_node)
                else:
                    self.open_nodes.append(better_node)

    return [self.start.pos]

