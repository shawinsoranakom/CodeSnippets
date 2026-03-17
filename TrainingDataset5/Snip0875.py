def search(self) -> Path | None:
    while self.fwd_bfs.node_queue or self.bwd_bfs.node_queue:
        current_fwd_node = self.fwd_bfs.node_queue.pop(0)
        current_bwd_node = self.bwd_bfs.node_queue.pop(0)

        if current_bwd_node.pos == current_fwd_node.pos:
            self.reached = True
            return self.retrace_bidirectional_path(
                current_fwd_node, current_bwd_node
            )

        self.fwd_bfs.target = current_bwd_node
        self.bwd_bfs.target = current_fwd_node

        successors = {
            self.fwd_bfs: self.fwd_bfs.get_successors(current_fwd_node),
            self.bwd_bfs: self.bwd_bfs.get_successors(current_bwd_node),
        }

        for bfs in [self.fwd_bfs, self.bwd_bfs]:
            for node in successors[bfs]:
                bfs.node_queue.append(node)

    if not self.reached:
        return [self.fwd_bfs.start.pos]
    return None
