def build_fusion_regions(
    gm: fx.GraphModule,
) -> dict[fx.Node, OrderedSet[fx.Node]]:
    """Build fusion regions from contiguous spans of fusible nodes.

    1. Identify contiguous spans of fusible nodes (separated by non-fusible nodes)
    2. Find connected components within each span
    3. Return regions that have 2+ non-view nodes

    This ensures fusion regions are strictly local - no reordering across
    non-fusible node boundaries.

    Returns a dict mapping each node to its fusion group (OrderedSet of nodes).
    """
    # Build node -> topo index map for sorting
    node_to_idx: dict[fx.Node, int] = {n: i for i, n in enumerate(gm.graph.nodes)}

    # Step 1: Get contiguous spans of fusible nodes
    spans = _get_contiguous_fusible_spans(gm)

    # Step 2: Find connected components within each span
    region_of: dict[fx.Node, OrderedSet[fx.Node]] = {}

    for span in spans:
        if len(span) < 2:
            continue

        components = _find_connected_components(span)

        for component in components:
            # Skip regions with fewer than 2 non-view nodes (views have no cost)
            non_view_count = sum(1 for n in component if not is_view_node(n))
            if non_view_count < 2:
                continue

            # Sort nodes in topological order to preserve original ordering
            sorted_component = sorted(component, key=lambda n: node_to_idx[n])
            node_set = OrderedSet(sorted_component)

            for node in sorted_component:
                region_of[node] = node_set

    return region_of