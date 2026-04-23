def dead_node_elimination(self) -> None:
        """
        Remove any nodes without users
        """
        if not config.use_dce:
            return

        # self.nodes is in topological order, so by iterating in reverse order
        # we have visited (and potentially removed) all users before visiting a
        # given node.
        updated_nodes = []
        for node in reversed(self.nodes):

            def can_eliminate_user(user: NodeUser) -> bool:
                return user.is_weak or user.get_name() in V.graph.removed_operations

            active_buffers = False
            for buf in node.get_outputs():
                can_eliminate = all(can_eliminate_user(u) for u in buf.users)
                if can_eliminate:
                    log.debug("removed dead buffer: %s", buf.get_name())
                    V.graph.removed_buffers.add(buf.get_name())
                else:
                    active_buffers = True

            can_eliminate = not node.has_side_effects() and not active_buffers

            if not can_eliminate:
                updated_nodes.append(node)
            else:
                # dead code
                log.debug("removed dead operation: %s", node.get_name())
                V.graph.removed_operations.add(node.get_name())
                for read in node.read_writes.reads:
                    if read.name in self.name_to_buf:
                        users = self.name_to_buf[read.name].users
                        self.name_to_buf[read.name].users = [
                            u for u in users if u.node.get_name() != node.get_name()
                        ]
        self.nodes = list(reversed(updated_nodes))

        # Prune any WeakDeps no longer needed
        for node in self.nodes:
            node.prune_weak_deps()