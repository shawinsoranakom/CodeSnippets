def get_fusion_candidates(
    rule: GroupBatchFusionBase,
    root_node: torch.fx.Node,
    fused_set: OrderedSet[torch.fx.Node],
) -> collections.defaultdict[Any, list[torch.fx.Node]]:
    """
    Search fusion candidates for a specific rule using BFS starting from the root node.
    We only search the subgraph within graph_search_options["max_fuse_search_depth"].
    """
    q: collections.deque[tuple[int, torch.fx.Node]] = collections.deque()

    candidate_dict: collections.defaultdict[Any, list[torch.fx.Node]] = (
        collections.defaultdict(list)
    )

    if root_node.target in SEARCH_EXCLUSIONS:
        return candidate_dict

    visited_set = OrderedSet[torch.fx.Node]()

    for next_node in root_node.all_input_nodes:
        q.append((1, next_node))
        visited_set.add(next_node)

    while len(q) > 0:
        depth, node = q.popleft()

        if node in fused_set:
            continue

        key = rule.match(node)
        if key is not None:
            candidate_nodes = candidate_dict[key]
            if node not in candidate_nodes:
                candidate_nodes.append(node)
        else:
            if depth < rule.graph_search_options["max_fuse_search_depth"]:
                for next_node in node.all_input_nodes:
                    if next_node not in visited_set:
                        visited_set.add(next_node)
                        q.append((depth + 1, next_node))

    return candidate_dict