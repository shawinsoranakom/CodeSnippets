def process_collective_bucket(
    g: torch.fx.Graph,
    bucket_nodes: list[torch.fx.Node],
    fn_to_trace: Callable[..., list[torch.Tensor]],
    trace_args_fn: Callable[[list[torch.fx.Node]], tuple[Any, ...]],
    insert_before: torch.fx.Node | None = None,
    wait_insertion_point: torch.fx.Node | None = None,
) -> tuple[list[torch.fx.Node], dict[torch.fx.Node, torch.fx.Node]]:
    """
    Process a single bucket of collective operation nodes with flexible insertion control.

    Args:
        g: The graph to modify
        bucket_nodes: Nodes in the current bucket to process
        fn_to_trace: Function to trace and insert
        trace_args_fn: Function to create trace arguments from inputs
        insert_before: Where to insert the traced function (default: after last bucket node)
        wait_insertion_point: If provided, move all nodes from wait() onwards to before this node

    Returns:
        new_nodes: List of all newly inserted nodes
        replacements: Dictionary mapping old wait nodes to new output nodes
    """
    # Collect inputs and waits from current bucket
    bucket_ins: list[torch.fx.Node] = []
    bucket_waits: list[torch.fx.Node] = []
    ag_node_to_pre_nodes: dict[torch.fx.Node, list[torch.fx.Node]] = defaultdict(list)

    for n in bucket_nodes:
        assert len(n.users) == 1, f"Expected single user for {n}, got {n.users}"
        wait_n = next(iter(n.users))

        # Handle convert_element_type operations (for all_gather)
        node_in = n.args[0]
        if has_mergeable_all_gather_convert_dtype(n):
            # pyrefly: ignore [bad-argument-type]
            ag_node_to_pre_nodes[n].append(node_in)
            # pyrefly: ignore [missing-attribute]
            node_in = node_in.args[0]

        assert isinstance(node_in, torch.fx.Node)  # Ensure node_in is a Node
        bucket_ins.append(node_in)
        bucket_waits.append(wait_n)

    # Create trace arguments
    trace_args = trace_args_fn(bucket_ins)

    # Determine insertion point
    if insert_before is None:
        insert_before = bucket_nodes[-1].next

    # Insert traced function and get replacements + new nodes
    replacements, new_nodes = _insert_fn_trace_before_node(
        g,
        fn_to_trace,
        trace_args,
        insert_before,
        bucket_ins,
        bucket_waits,
    )

    # If requested, move wait nodes and everything after to specified location
    if wait_insertion_point is not None:
        # Find the first wait node in new_nodes
        wait_start_idx = None
        for i, node in enumerate(new_nodes):
            if is_wait_tensor(node):
                wait_start_idx = i
                break

        # Move all nodes from wait onwards (including the wait)
        if wait_start_idx is not None:
            nodes_to_move = new_nodes[wait_start_idx:]
            for node in nodes_to_move:
                wait_insertion_point.prepend(node)

    # Preserve metadata from original collective nodes to new bucketed nodes
    if bucket_nodes:
        overlap_log.debug(
            "Bucketing nodes: %s, New nodes: %s",
            ",".join([n.name for n in bucket_nodes]),
            ",".join([n.name for n in new_nodes]),
        )
    _populate_node_meta(bucket_nodes, new_nodes)

    # Erase old nodes
    for node, wait_n in zip(bucket_nodes, bucket_waits):
        g.erase_node(wait_n)
        g.erase_node(node)
        # Erase any convert_element_type nodes we tracked
        for pre_node in reversed(ag_node_to_pre_nodes[node]):
            g.erase_node(pre_node)

    return new_nodes, replacements