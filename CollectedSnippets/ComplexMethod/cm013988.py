def _detect_cycles(
    graph: Graph, node_to_additional_deps: dict[Node, OrderedSet[Node]]
) -> str:
    # States: 0=Unvisited, 1=Visiting, 2=Visited(Safe)
    state: dict[Node, int] = {}

    for root in reversed(graph.nodes):
        if root in state:
            continue

        # Stack holds (current_node, children_iterator).
        # Using an iterator allows us to pause and resume processing a node's children.
        stack = [(root, iter(_get_flat_args_unique(root, node_to_additional_deps)))]
        state[root] = 1  # Visiting

        while stack:
            parent, children = stack[-1]

            try:
                child = next(children)

                if not isinstance(child, Node):
                    continue

                child_state = state.get(child, 0)

                if child_state == 1:
                    # Back-edge: child is on the current DFS path -> cycle
                    cycle_path = [node for node, _ in stack] + [child]
                    return f"cycle detected in path: {cycle_path}"

                if child_state == 0:
                    state[child] = 1
                    stack.append(
                        (
                            child,
                            iter(_get_flat_args_unique(child, node_to_additional_deps)),
                        )
                    )
                # child_state == 2 means already verified safe; skip.

            except StopIteration:
                # All children processed — mark safe and pop.
                stack.pop()
                state[parent] = 2

    return "no cycle detected"