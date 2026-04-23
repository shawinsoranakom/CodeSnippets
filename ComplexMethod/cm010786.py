def _get_backward_memory_from_topologically_sorted_graph(
        self,
        node_graph: nx.DiGraph,
        node_memories: dict[str, float],
        saved_nodes_set: set[str],
        peak_memory_after_forward_pass: float,
    ) -> list[tuple[float, str]]:
        """
        Simulates the backward pass and keeps track of the peak memory usage.

        High Level Steps:
            1. Set Initial Peak/Current Memory
                Allows you to set the peak memory after the forward pass, but typically this is
                the sum of the estimated memory of the saved nodes.
            2. Perform a reverse topological sort of the node_graph.
                If full graph is defined then will sort the full graph and only process the subset
                of nodes in the node_graph.
            3. Iterate through the sorted graph nodes.
                If the node is saved then just drop it's memory from current memory.
                If the node is not saved then add it's memory to current memory and then traverse it's
                predecessors to simulate recomuptation chain. Will check if new peak memory after all
                predecessors are processed.

        Args:
            node_graph (nx.DiGraph): A directed graph representing the recomputable forward nodes.
            saved_nodes_set (Set[str]): A set of node names that are saved.
            peak_memory_after_forward_pass (float): The peak memory usage after the forward pass.
        """
        current_memory = [
            (peak_memory_after_forward_pass, "Initial Peak/Current Memory")
        ]
        already_computed = set()
        sorted_nodes = list(reversed(list(nx.topological_sort(node_graph))))
        dependencies_computed = set()

        for node in sorted_nodes:
            if node in saved_nodes_set or node in already_computed:
                current_memory.append(
                    (
                        current_memory[-1][0] - node_memories[node],
                        f"Dropping Node(already saved): {node}",
                    )
                )
                continue

            already_computed.add(node)
            current_memory.append(
                (
                    current_memory[-1][0] + node_memories[node],
                    f"Recomputing Node: {node}",
                )
            )
            # Create a queue of dependencies required for recomputation
            predecessor_queue = deque(
                [
                    dependency
                    # pyrefly: ignore [bad-unpacking]
                    for dependency, v in node_graph.in_edges(node)
                    if dependency not in already_computed
                ]
            )
            while predecessor_queue:
                dep = predecessor_queue.popleft()
                already_computed.add(dep)
                dependencies_computed.add(dep)
                current_memory.append(
                    (
                        current_memory[-1][0] + node_memories[dep],
                        f"Recomputing Predecessor of {node}: {dep}",
                    )
                )
                # Add predecessors of the predecessor to the queue if they haven't been recomputed yet
                # pyrefly: ignore [bad-unpacking]
                for dependency_of_dependency, _ in node_graph.in_edges(dep):
                    if (
                        dependency_of_dependency in already_computed
                        or dependency_of_dependency in saved_nodes_set
                        or dependency_of_dependency in predecessor_queue
                    ):
                        continue
                    predecessor_queue.append(dependency_of_dependency)
            dependencies_computed.clear()
            current_memory.append(
                (current_memory[-1][0] - node_memories[node], f"Dropping Node: {node}")
            )
        return current_memory