def legalize_graph(gm: torch.fx.GraphModule) -> torch.fx.GraphModule:
    """
    Replace the graph of the given GraphModule with one that contains the same nodes as the
    original, but in topologically sorted order.

    This is used by the merge_matmul transformation below, which disturbs the topologically sorted
    order of its input GraphModule, so that this order is restored before further transformation.

    Arguments:
        gm: The graph module to topologically sort. It is modified in-place.

    Returns:
        The graph module in-place sorted

    Warning:
        This topological sort is NOT stable, it will NOT preserve the original node order.
        If you need a stable topological sort, use stable_topological_sort instead.
    """

    # These operators are used for making runtime assertions before any
    # data-dependent operators occur. We want to prioritize sorting these to
    # ensure that these assertions appear before any data-dependent operations
    # in the graph.
    PRIORITIZED_OPS = [
        operator.add,
        operator.mul,
        operator.sub,
        operator.floordiv,
        operator.truediv,
        operator.mod,
        operator.le,
        operator.lt,
        operator.ge,
        operator.gt,
        operator.eq,
        operator.ne,
        torch.ops.aten.sym_constrain_range.default,
        torch.ops.aten.sym_constrain_range_for_size.default,
        torch.ops.aten._assert_async.msg,
        torch.ops.aten.scalar_tensor.default,
        torch.ops.aten._assert_scalar.default,
    ]

    indeg = dict.fromkeys(gm.graph.nodes, 0)
    new_graph = torch.fx.Graph()
    # Track how many unfulfilled dependencies each node has
    for node in gm.graph.nodes:
        for user in node.users:
            indeg[user] += 1
    queue: collections.deque[torch.fx.Node] = collections.deque()
    # Add all nodes with no dependencies to the queue
    for node in gm.graph.nodes:
        if indeg[node] == 0:
            queue.append(node)
    env: dict[torch.fx.Node, torch.fx.Node] = {}
    # Pop nodes from the queue, and add nodes that have had all their
    # dependencies fulfilled
    while len(queue) > 0:
        cur = queue.popleft()
        env[cur] = new_graph.node_copy(cur, lambda x: env[x])
        for user in cur.users:
            indeg[user] -= 1
            if indeg[user] == 0:
                if user.op == "call_function" and user.target in PRIORITIZED_OPS:
                    queue.appendleft(user)
                else:
                    queue.append(user)
    # If the new graph's size is not as large as the old one, then there must be
    # a cycle (i.e. some node's dependencies were not satisfied.)
    if len(new_graph.nodes) < len(gm.graph.nodes):
        raise RuntimeError(
            f"Input graph has cycles, unable to add {[node for node in indeg if indeg[node] != 0]}"
        )
    new_graph._codegen = gm.graph._codegen
    gm.graph = new_graph
    return gm