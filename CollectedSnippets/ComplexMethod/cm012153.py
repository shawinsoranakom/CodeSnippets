def build_memory_profile(
    graph: fx.Graph,
    is_releasable: Callable[[fx.Node], bool],
    size_of: Callable[[int | torch.SymInt], int] | None = None,
) -> list[int]:
    """
    Function to estimate the memory profile of an input FX graph.

    Args:
    - graph (fx.Graph): The input FX graph for which the memory profile
      is to be estimated.
    - is_releasable (Callable[[fx.Node], bool]): A function that
      determines if a node's memory can be released (e.g. primal nodes
      cannot be released).
    - size_of (Callable[[int | torch.SymInt], int]): A function that converts
      byte counts (possibly symbolic) to concrete integers.

    Returns:
    - List[int]: A list representing the memory profile over the execution
      of the graph, where each entry corresponds to the memory usage at
      a particular point in the execution.
    """

    size_of = size_of or _size_of_default
    nodes = list(graph.nodes)
    alias_info = GraphAliasTracker(nodes)

    # Build memory profile
    current_memory = 0

    for node in itertools.chain(
        graph.find_nodes(op="placeholder"), graph.find_nodes(op="get_attr")
    ):
        for storage_key in alias_info.get_fresh_allocations(node):
            if device_filter(storage_key.device):
                current_memory += size_of(storage_key.storage.nbytes())

    memory_profile = [current_memory]

    for node in nodes:
        if node.op in ("placeholder", "get_attr", "output"):
            continue

        # Process allocations
        for storage_key in alias_info.get_fresh_allocations(node):
            if device_filter(storage_key.device):
                current_memory += size_of(storage_key.storage.nbytes())

        memory_profile.append(current_memory)

        # Process deallocations
        # pyrefly: ignore [bad-assignment]
        for storage_key in alias_info.get_storages_last_used(node):
            allocator = alias_info.storage_to_allocator[storage_key]
            if is_releasable(allocator):
                if device_filter(storage_key.device):
                    current_memory -= size_of(storage_key.storage.nbytes())

        memory_profile.append(current_memory)

    return memory_profile