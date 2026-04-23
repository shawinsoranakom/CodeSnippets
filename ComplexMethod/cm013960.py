def fully_expand_region_group(
    regions: list[Region],
    seen_nodes: set[Node],
    node_to_recursive_ancestors: dict[Node, set[Node]],
    is_identical_fn: Callable[[Node, Node], bool],
) -> None:
    debug_log("--------------------------------------------------")
    debug_log("expanding new region group: %s", regions)

    # All regions should start with 1 node
    assert all(len(region) == 1 for region in regions)
    region_wrappers = [
        RegionWrapper(region, node_to_recursive_ancestors) for region in regions
    ]

    nodes_to_add = OrderedSet[Node]()
    current_node = region_wrappers[0].next_candidate()

    # No children
    if current_node is None:
        return

    # Loop incrementally adding new nodes to each region
    # regions are only expanded if the node to add is valid
    # for ALL regions
    while current_node:
        add_to_all_regions = not region_wrappers[0].will_inclusion_create_cycle(
            current_node
        )
        nodes_to_add.clear()
        nodes_to_add.add(current_node)
        for region_wrapper in region_wrappers[1:]:
            candidate = region_wrapper.next_candidate()

            debug_log("--------------------")
            debug_log(
                "considering candidate: %s, cur_node: %s", candidate, current_node
            )

            if not candidate or not add_to_all_regions:
                add_to_all_regions = False
                continue

            debug_log(
                "candidate in previously claimed nodes?: %s", candidate in seen_nodes
            )
            debug_log("is_identical: %s", is_identical_fn(candidate, current_node))

            add_to_all_regions &= (
                candidate not in seen_nodes
                and candidate not in nodes_to_add
                and candidate.op != "placeholder"
                and candidate.op != "get_attr"
                and is_identical_fn(candidate, current_node)
                and not region_wrapper.will_inclusion_create_cycle(candidate)
            )
            nodes_to_add.add(candidate)

            debug_log(f"add_to_all_regions: {add_to_all_regions}")
            debug_log("--------------------")

        if add_to_all_regions:
            assert len(region_wrappers) == len(nodes_to_add), (
                "Number of nodes to add must equal the number of regions"
            )
            for region_wrapper, node in zip(region_wrappers, nodes_to_add):
                region_wrapper.add(node)
                debug_log("adding %s's children", node)
                debug_log("%s %s", node.args, list(node.kwargs.items()))
                seen_nodes.add(node)

        current_node = region_wrappers[0].next_candidate()

    # Ensure regions are sorted in topological order
    for region in regions:
        region.reverse()

    debug_log("end expand new region group: %s", regions)
    debug_log("--------------------------------------------------")