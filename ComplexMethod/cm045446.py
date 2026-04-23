def dfs(node_name: str) -> bool:
            visited.add(node_name)
            rec_stack.add(node_name)
            path.append(node_name)
            cycle = False

            for edge in self.nodes[node_name].edges:
                target = edge.target
                if target not in visited:
                    if dfs(target):
                        cycle = True
                elif target in rec_stack:
                    # Found a cycle → extract the cycle
                    cycle_start_index = path.index(target)
                    cycle_nodes = path[cycle_start_index:]
                    cycle_edges: List[DiGraphEdge] = []
                    for n in cycle_nodes:
                        cycle_edges.extend(self.nodes[n].edges)
                    if all(edge.condition is None and edge.condition_function is None for edge in cycle_edges):
                        raise ValueError(
                            f"Cycle detected without exit condition: {' -> '.join(cycle_nodes + cycle_nodes[:1])}"
                        )
                    cycle = True  # Found cycle, but it has an exit condition

            rec_stack.remove(node_name)
            path.pop()
            return cycle