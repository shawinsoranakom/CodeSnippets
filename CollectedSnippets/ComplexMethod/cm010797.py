def reorder_for_prefetch(
    nodes_list: list[fx.Node],
    reload_patterns: dict[fx.Node, ReloadNodeInfo],
) -> None:
    """
    Reorder nodes to prefetch reload operations by directly manipulating the graph.

    This follows the algorithm as follows:
    - Go through nodes in reverse order
    - When encountering a reload pattern, add it to a queue with its transfer time
    - When encountering a compute node, use its runtime to satisfy overlap requirements
    - Place reload patterns when their overlap requirement is satisfied
    - When encountering placeholder nodes, flush queue as reloads cannot move before inputs
    """

    # Build a set of all nodes in reload groups for quick lookup
    reload_group_nodes_set: set[fx.Node] = set()
    for pattern in reload_patterns.values():
        reload_group_nodes_set.update(pattern.reload_group_nodes)

    # Queue to hold reload group nodes waiting to be placed (FIFO)
    reload_queue: list[ReloadQueueEntry] = []

    # Loop through nodes in reverse
    for node in reversed(nodes_list):
        if node.op == "output":
            continue
        elif node.op == "placeholder":
            # Flush queue - place all remaining reloads after the last placeholder
            while reload_queue:
                entry: ReloadQueueEntry = reload_queue.pop(0)
                for reload_group_node in reversed(entry.pattern.reload_group_nodes):
                    node.append(reload_group_node)
            break
        elif node in reload_patterns:
            pattern: ReloadNodeInfo = reload_patterns[node]
            reload_queue.append(
                ReloadQueueEntry(
                    pattern=pattern, remaining_time_ms=pattern.transfer_time_ms
                )
            )
        elif node in reload_group_nodes_set:
            continue
        else:
            if not reload_queue:
                continue
            compute_runtime_ms: float = (
                benchmark_node(node) if is_compute_node(node) else 0
            )
            reload_queue[0].remaining_time_ms -= compute_runtime_ms

            # Pop and place reload if its remaining time is satisfied (<= 0)
            if reload_queue[0].remaining_time_ms <= 0:
                entry: ReloadQueueEntry = reload_queue.pop(0)
                for reload_group_node in entry.pattern.reload_group_nodes:
                    node.prepend(reload_group_node)