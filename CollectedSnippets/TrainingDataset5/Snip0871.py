def search(self) -> list[TPosition]:
    while self.fwd_astar.open_nodes or self.bwd_astar.open_nodes:
        self.fwd_astar.open_nodes.sort()
        self.bwd_astar.open_nodes.sort()
        current_fwd_node = self.fwd_astar.open_nodes.pop(0)
        current_bwd_node = self.bwd_astar.open_nodes.pop(0)

        if current_bwd_node.pos == current_fwd_node.pos:
            return self.retrace_bidirectional_path(
                current_fwd_node, current_bwd_node
            )

        self.fwd_astar.closed_nodes.append(current_fwd_node)
        self.bwd_astar.closed_nodes.append(current_bwd_node)

        self.fwd_astar.target = current_bwd_node
        self.bwd_astar.target = current_fwd_node

        successors = {
            self.fwd_astar: self.fwd_astar.get_successors(current_fwd_node),
            self.bwd_astar: self.bwd_astar.get_successors(current_bwd_node),
        }

        for astar in [self.fwd_astar, self.bwd_astar]:
            for child_node in successors[astar]:
                if child_node in astar.closed_nodes:
                    continue

                if child_node not in astar.open_nodes:
                    astar.open_nodes.append(child_node)
                else:
                    better_node = astar.open_nodes.pop(
                        astar.open_nodes.index(child_node)
                    )

                    if child_node.g_cost < better_node.g_cost:
                        astar.open_nodes.append(child_node)
                    else:
                        astar.open_nodes.append(better_node)

    return [self.fwd_astar.start.pos]
