def get_fwd_bwd_interactions(
    fwd_graph: fx.Graph,
    bwd_graph: fx.Graph,
    size_of: Callable[[int | torch.SymInt], int] | None = None,
) -> tuple[int, OrderedSet[str]]:
    """
    Analyze the interactions between the forward (fwd) and backward (bwd) graphs
    to determine memory usage characteristics.

    Args:
    - fwd_graph (fx.Graph): The forward graph representing the forward pass.
    - bwd_graph (fx.Graph): The backward graph representing the backward pass.
    - size_of (Callable[[int | torch.SymInt], int]): A function that converts
      byte counts (possibly symbolic) to concrete integers.

    Returns:
    - tuple[int, OrderedSet[str]]: A tuple containing:
        1. The baseline memory usage during the backward pass, accounting for
           storages that persist from the forward pass (i.e., in fwd output but
           not in bwd input).
        2. A set of node names whose storage cannot be released during the bwd pass.
           These include nodes that use storage from primals or are in bwd input
           but not in fwd output.
    """

    size_of = size_of or _size_of_default

    # Build alias info for forward graph
    fwd_nodes = list(fwd_graph.nodes)
    fwd_alias_info = GraphAliasTracker(fwd_nodes)

    # Identify storages allocated by primal placeholder nodes
    primal_storages: OrderedSet[StorageKey] = OrderedSet()
    for node in fwd_graph.find_nodes(op="placeholder"):
        if node.name.startswith("primals"):
            primal_storages.update(fwd_alias_info.get_fresh_allocations(node))

    # Get storages in forward output
    fwd_output_node = next(iter(reversed(fwd_graph.nodes)))[-1]
    assert fwd_output_node.op == "output"
    fwd_output_storages = fwd_alias_info.get_storage_uses(fwd_output_node)

    # Node names that should not be deleted during memory profile estimation of bwd_graph
    do_not_delete: OrderedSet[str] = OrderedSet()

    # Collect all storages in backward inputs and identify nodes to not delete
    bwd_input_storages: OrderedSet[StorageKey] = OrderedSet()
    for node in bwd_graph.find_nodes(op="placeholder"):
        node_storages = GraphAliasTracker._get_output_storages(node)
        bwd_input_storages.update(node_storages)

        # Check if this node uses primal storage
        if node_storages & primal_storages:
            do_not_delete.add(node.name)

        # Check if this node's storages are not in forward outputs
        # (meaning it's an external input to backward pass)
        if not (node_storages & fwd_output_storages):
            do_not_delete.add(node.name)

    # Calculate baseline memory: storages in fwd output but not in bwd input
    # These storages persist throughout the backward pass
    baseline_storages = fwd_output_storages - bwd_input_storages
    bwd_baseline_memory = 0
    for storage_key in baseline_storages:
        if storage_key.device.type != "cpu":
            bwd_baseline_memory += size_of(storage_key.storage.nbytes())

    return bwd_baseline_memory, do_not_delete