def collapse_fusion_regions(
    gm: fx.GraphModule,
    region_of: dict[fx.Node, OrderedSet[fx.Node]],
) -> dict[fx.Node, FusionRegion]:
    """
    Collapse fusion regions into call_module nodes using fuse_by_partitions.
    Returns new_region_of mapping module nodes to FusionRegions.
    """
    from torch.fx.passes.utils.fuser_utils import fuse_by_partitions

    if not region_of:
        return {}

    # Get unique node sets (regions with <2 nodes already filtered in build_fusion_regions)
    unique_regions: list[tuple[OrderedSet[fx.Node], int]] = []
    seen_region_ids: OrderedSet[int] = OrderedSet()
    for node_set in region_of.values():
        region_id = id(node_set)
        if region_id not in seen_region_ids:
            seen_region_ids.add(region_id)
            unique_regions.append((node_set, region_id))

    if not unique_regions:
        return {}

    # Log graph before fusion
    trace_structured(
        "artifact",
        metadata_fn=lambda: {
            "name": "fusion_regions_before",
            "encoding": "string",
        },
        payload_fn=lambda: gm.print_readable(print_output=False),
    )

    # Build partitions list for fuse_by_partitions
    partitions = [dict.fromkeys(nodes) for nodes, _ in unique_regions]

    # Fuse all partitions at once
    fuse_by_partitions(gm, partitions, prefix="_fusion_region_")

    # Log graph after fusion
    trace_structured(
        "artifact",
        metadata_fn=lambda: {
            "name": "fusion_regions_after",
            "encoding": "string",
        },
        payload_fn=lambda: gm.print_readable(print_output=False),
    )

    # Build new_region_of by finding the call_module nodes
    new_region_of: dict[fx.Node, FusionRegion] = {}

    for region_idx in range(len(unique_regions)):
        subgraph_name = f"_fusion_region_{region_idx}"

        # Find the call_module node
        module_nodes = list(gm.graph.find_nodes(op="call_module", target=subgraph_name))
        assert len(module_nodes) == 1, (
            f"Expected 1 call_module for {subgraph_name}, got {len(module_nodes)}"
        )
        module_node = module_nodes[0]

        subgraph_module = getattr(gm, subgraph_name)

        # Create FusionRegion with all required info
        region = FusionRegion(
            subgraph_node=module_node,
            subgraph_module=subgraph_module,
        )

        new_region_of[module_node] = region

    return new_region_of