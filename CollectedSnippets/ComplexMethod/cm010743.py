def _canonical_node_names(graph: torch.fx.Graph) -> dict[torch.fx.Node, str]:
    """Build a canonical name mapping for graph nodes using Kahn's algorithm.

    Returns a dict mapping each node to a deterministic name like "node_0",
    "node_1", etc. The mapping is invariant to the original node ordering and
    naming, so structurally equivalent graphs (e.g., traced with different dict
    iteration orders across distributed ranks) produce identical mappings.

    Does NOT modify the graph.
    """
    cone = _cone_hashes(graph)

    indeg: dict[torch.fx.Node, int] = dict.fromkeys(graph.nodes, 0)
    for node in graph.nodes:
        for user in node.users:
            indeg[user] += 1

    canonical_idx: dict[torch.fx.Node, int] = {}

    def _canonical_key(node: torch.fx.Node) -> tuple[Any, ...]:
        if node.op == "placeholder":
            val = node.meta.get("val")
            if isinstance(val, torch.Tensor):
                # Exclude shape: different ranks may have different input
                # shapes (e.g., shard sizes) for structurally identical graphs.
                meta_key: tuple[Any, ...] = (
                    str(val.dtype),
                    val.requires_grad,
                )
            elif isinstance(val, torch.SymInt):
                meta_key = ("symint",)
            else:
                meta_key = ()
            return (0, meta_key, cone[node])
        elif node.op == "get_attr":
            return (1, str(node.target))
        elif node.op == "output":
            return (3,)
        else:
            input_indices = tuple(canonical_idx[n] for n in node.all_input_nodes)
            return (2, str(node.target), input_indices)

    # Seed the heap with nodes that have no dependencies.
    # The counter ensures deterministic ordering when keys are equal.
    counter = 0
    ready: list[tuple[tuple[Any, ...], int, fx.Node]] = []
    for node in graph.nodes:
        if indeg[node] == 0:
            heapq.heappush(ready, (_canonical_key(node), counter, node))
            counter += 1

    canonical_order: list[fx.Node] = []

    while ready:
        _, _, cur = heapq.heappop(ready)
        canonical_order.append(cur)
        canonical_idx[cur] = len(canonical_idx)

        for user in cur.users:
            indeg[user] -= 1
            if indeg[user] == 0:
                heapq.heappush(ready, (_canonical_key(user), counter, user))
                counter += 1

    return {node: f"node_{i}" for i, node in enumerate(canonical_order)}