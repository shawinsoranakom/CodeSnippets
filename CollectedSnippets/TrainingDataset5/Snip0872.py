def search(self) -> Path | None:
    while self.node_queue:
        current_node = self.node_queue.pop(0)

        if current_node.pos == self.target.pos:
            self.reached = True
            return self.retrace_path(current_node)

        successors = self.get_successors(current_node)

        for node in successors:
            self.node_queue.append(node)

    if not self.reached:
        return [self.start.pos]
    return None
