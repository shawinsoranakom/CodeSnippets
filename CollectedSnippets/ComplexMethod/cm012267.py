def greedy_bucket_collective_by_mb(
    gm: torch.fx.GraphModule,
    bucket_cap_mb_by_bucket_idx: Callable[[int], float],
    filter_node: Callable[[torch.fx.Node], bool],
    node_group_key: Callable[[torch.fx.Node], Any],
    filter_wait_node: Callable[[torch.fx.Node], bool] | None = None,
) -> list[list[torch.fx.Node]]:
    """
    Bucketing adjacent collectives with equal node_group_key.
    We can not bucket non adjacent collectives,
    as this will effectively change the order of collectives.
    Reordering can lead to different order on different ranks.
    """
    g = gm.graph
    found_candidates = False
    for node in g.nodes:
        if filter_node(node):
            found_candidates = True
            break
    if not found_candidates:
        return []

    # TODO: pearce kelly algorithm for detecting cycles
    node_descendents = collect_node_descendants(gm.graph)

    nodes_groups: list[list[torch.fx.Node]] = []
    cur_group: list[torch.fx.Node] = []
    cur_group_key = None

    for node in g.nodes:
        if is_wait_tensor(node) and filter_node(node.args[0]):
            if (filter_wait_node is None) or filter_wait_node(node):
                coll_node = node.args[0]
                group_key = node_group_key(coll_node)
                if group_key == cur_group_key:
                    cur_group.append(coll_node)
                else:
                    if len(cur_group) > 1:
                        nodes_groups.append(cur_group)
                    cur_group = [coll_node]
                    cur_group_key = group_key

    if len(cur_group) > 1:
        nodes_groups.append(cur_group)

    buckets: list[list[torch.fx.Node]] = []
    for nodes in nodes_groups:
        cur_bucket: list[torch.fx.Node] = []
        cur_bucket_descendents: OrderedSet[torch.fx.Node] = OrderedSet()
        cur_bucket_size_bytes: int = 0
        cur_bucket_id: int = 0
        bucket_size_bytes = int(
            bucket_cap_mb_by_bucket_idx(cur_bucket_id) * 1024 * 1024
        )
        for node in nodes:
            if node in cur_bucket_descendents:
                # if there is a path from node to the current bucket, we cannot horizontally fuse (bucket)
                continue
            assert "val" in node.meta
            n_val = node.meta["val"]
            out_size_bytes = n_val.numel() * n_val.element_size()
            n_input_val = node.all_input_nodes[0].meta["val"]
            in_size_bytes = n_input_val.numel() * n_input_val.element_size()
            size_bytes = max(out_size_bytes, in_size_bytes)
            if cur_bucket_size_bytes + size_bytes > bucket_size_bytes and cur_bucket:
                # Current bucket is full, create new bucket
                if len(cur_bucket) > 1:
                    buckets.append(cur_bucket)
                cur_bucket = []
                cur_bucket_size_bytes = 0
                cur_bucket_id += 1
                cur_bucket_descendents = OrderedSet()
            cur_bucket_size_bytes += size_bytes
            cur_bucket.append(node)
            cur_bucket_descendents |= node_descendents[node]
        if len(cur_bucket) > 1:
            buckets.append(cur_bucket)
    return buckets