def get_nodes_in_cycle(self):
        # We'll dissolve the graph in reverse topological order to leave only the nodes in the cycle.
        # We're skipping some of the performance optimizations from the original TopologicalSort to keep
        # the code simple (and because having a cycle in the first place is a catastrophic error)
        blocked_by = { node_id: {} for node_id in self.pendingNodes }
        for from_node_id in self.blocking:
            for to_node_id in self.blocking[from_node_id]:
                if True in self.blocking[from_node_id][to_node_id].values():
                    blocked_by[to_node_id][from_node_id] = True
        to_remove = [node_id for node_id in blocked_by if len(blocked_by[node_id]) == 0]
        while len(to_remove) > 0:
            for node_id in to_remove:
                for to_node_id in blocked_by:
                    if node_id in blocked_by[to_node_id]:
                        del blocked_by[to_node_id][node_id]
                del blocked_by[node_id]
            to_remove = [node_id for node_id in blocked_by if len(blocked_by[node_id]) == 0]
        return list(blocked_by.keys())