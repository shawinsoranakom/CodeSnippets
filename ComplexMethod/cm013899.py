def _stable_topological_sort_impl(
    graph: torch.fx.Graph,
    node_to_additional_deps: dict[Node, OrderedSet[Node]],
    do_sort: bool = True,
) -> bool:
    # Nodes are in exactly one of these four collections:

    # - Nodes in `pending` are waiting to be processed (in reverse order):
    pending = list(reversed(graph.nodes))

    # - Nodes in `ready` have been processed and are already in the correct
    #   order.
    ready = OrderedSet[Node]()

    # - `waiting` is a mapping from a dependency to nodes which depend on that
    #   dependency.
    waiting = defaultdict(list)

    # - `outputs` are always at the end of the graph
    outputs = OrderedSet[Node]()

    # The cursor indicates the last processed node so we can add new nodes
    # after it.
    cursor = None
    while pending:
        node = pending.pop()

        if node.target == "output":
            outputs.add(node)
            assert not node.users, "output nodes should have no users"
            continue

        waiting_for = [
            x
            for x in _get_flat_args_unique(node, node_to_additional_deps)
            if x not in ready
        ]
        if waiting_for:
            # We have unprocessed input nodes. Might as well wait for the last
            # arg so an already sorted list will only recheck this node once.
            waiting[waiting_for[-1]].append(node)
        else:
            ready.add(node)
            if cursor and cursor.next is not node and do_sort:
                cursor.append(node)
            cursor = node
            # Mark the nodes that have been waiting for this node to finish as
            # ready to check again.
            pending.extend(reversed(waiting.pop(node, ())))

    ready.update(outputs)
    return not waiting and len(ready) == len(graph.nodes)