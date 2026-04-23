def get_freeable_input_buf(
    nodes: list[BaseSchedulerNode],
    graph_inputs: OrderedSet[str],
) -> dict[str, FreeableInputBuffer]:
    """
    Create and keep track of all input buffers that can be freed during the program

    Returns:
        A dictionary containing all freeable input buffers, keyed by their names.
    """

    def _dep_size_hint(dep: Dep) -> int:
        return V.graph.get_dep_size_hint(dep)

    # get freeable input buffers' successor nodes for memory lifetime (excludes is_fake WeakDeps)
    # and for ordering (includes all deps)
    dep_name_to_succ_nodes: dict[str, OrderedSet[BaseSchedulerNode]] = (
        collections.defaultdict(OrderedSet)
    )
    dep_name_to_succ_nodes_for_ordering: dict[str, OrderedSet[BaseSchedulerNode]] = (
        collections.defaultdict(OrderedSet)
    )
    dep_name_to_size: dict[str, int] = dict()

    for node in nodes:
        for dep in node.read_writes.reads:
            if dep.name in graph_inputs:
                if not is_nonfreeable_buffers(dep):
                    # All deps contribute to ordering, but fake weak deps do not contribute to
                    # memory liveness
                    dep_name_to_succ_nodes_for_ordering[dep.name].add(node)
                    dep_name_to_size[dep.name] = _dep_size_hint(dep)
                    if not (isinstance(dep, WeakDep) and dep.is_fake):
                        dep_name_to_succ_nodes[dep.name].add(node)

    # create FreeableInputBuffer objects and add them to the returned dictionary
    name_to_freeable_input_buf: dict[str, FreeableInputBuffer] = dict()
    for dep_name in dep_name_to_succ_nodes_for_ordering:
        name_to_freeable_input_buf[dep_name] = FreeableInputBuffer(
            dep_name,
            MemoryPlanningInfoForBuffer(
                size_free=dep_name_to_size[dep_name],
                succ_nodes=dep_name_to_succ_nodes[dep_name],
                succ_nodes_for_ordering=dep_name_to_succ_nodes_for_ordering[dep_name],
            ),
        )
    return name_to_freeable_input_buf