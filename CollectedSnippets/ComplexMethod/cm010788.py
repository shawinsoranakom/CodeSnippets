def _create_recomputable_node_only_graph_with_larger_graph_context(
        self,
    ) -> nx.DiGraph:
        # Create a dictionary to store the reachable nodes for each node
        all_recomputable_banned_nodes_set = set(self.all_recomputable_banned_nodes)

        reachable_nodes = {}
        for node in all_recomputable_banned_nodes_set:
            # Use BFS to find all reachable nodes
            predecessors = dict(nx.bfs_predecessors(self.full_joint_nx_graph, node))
            reachable_recomputable_nodes = set(predecessors.keys()).intersection(
                all_recomputable_banned_nodes_set
            )
            reachable_nodes[node] = reachable_recomputable_nodes
        # Create the candidate graph
        candidate_graph = nx.DiGraph()
        candidate_graph.add_nodes_from(all_recomputable_banned_nodes_set)
        for node1 in all_recomputable_banned_nodes_set:
            for node2 in reachable_nodes[node1]:
                # Check if there is an overlapping path
                overlapping_path = False
                for intermediate_node in reachable_nodes[node1]:
                    if (
                        intermediate_node != node2
                        and node2 in reachable_nodes[intermediate_node]
                    ):
                        overlapping_path = True
                        break
                if not overlapping_path:
                    candidate_graph.add_edge(node1, node2)
        return candidate_graph