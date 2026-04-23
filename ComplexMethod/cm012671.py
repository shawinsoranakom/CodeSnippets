def _default_custom_combo_kernel_horizontal_partition(
    nodes: list[BaseSchedulerNode],
    triton_scheduling: SIMDScheduling,
    node_info_map: dict[BaseSchedulerNode, NodeInfo],
) -> list[list[BaseSchedulerNode]]:
    """Horizontally partition the given list of nodes into a list of list of nodes where each sublist
    represents a partition. Nodes in different partitions are implemented in different combo kernels.
    Nodes in the same partition are likely to be implemented
    in the same combo kernel, but subject to subsequent restrictions like CUDA limits for number of args.

    Input arguments:
        nodes: a list of fused scheduler nodes to partition.
        triton_scheduling: TritonScheduling instance.
        node_info_map: a map from node to NodeInfo NamedTuple
    Output:
        a list of list of nodes with each sublist representing a partition.

    The default algorithm is to partition nodes based on the following rules:
        1) nodes with the same number of block dimensions are grouped together.
        2) large pointwise nodes (numels greater than LARGE_NUMELS) are separated from other nodes.
        3) large reduce nodes are separated from other nodes.
    """

    assert len(nodes) >= 1

    # first partition nodes based on number of block dimensions
    tilings = [node_info_map[n].tiling for n in nodes]

    max_dims = max(len(t) for t in tilings)
    nodes_per_ndim: list[list[BaseSchedulerNode]] = []
    for i in range(2, max_dims + 1):
        group_per_dim = [n for n, t in zip(nodes, tilings) if len(t) == i]
        reduction = [
            n for n in group_per_dim if node_info_map[n].features.is_reduction()
        ]
        not_reduction = [n for n in group_per_dim if n not in reduction]
        # rnumel > 2048 usually has long execution time
        # BaseSchedulerNode.group[-1][-1] is rnumel for reduction nodes
        # Scheduling heuristic: separate long reductions (rnumel > 2048).
        # Uses optimization_hint with fallback=1 so unbacked defaults to short reduction.
        long_reduction = [
            n
            for n in reduction
            if V.graph.sizevars.optimization_hint(n.group[-1][-1], fallback=1) > 2048  # type: ignore[arg-type]
        ]
        short_reduction = [n for n in reduction if n not in long_reduction]
        if long_reduction:
            log.debug(
                "ComboKernels: %d long reduction nodes are separated",
                len(long_reduction),
            )
        large_pointwise = [
            n
            for n in not_reduction
            if not node_info_map[n].features.is_reduction()
            and len(node_info_map[n].tiling) == 2
            and V.graph.sizevars.optimization_hint(
                node_info_map[n].tiling["x"], fallback=1
            )
            > LARGE_NUMELS  # type: ignore[arg-type]
        ]
        if large_pointwise:
            # TODO benchmark the performance when large pointwise nodes combining with others
            log.debug(
                "ComboKernels: %d large pointwise nodes are separated",
                len(large_pointwise),
            )
            not_reduction = [n for n in not_reduction if n not in large_pointwise]
            nodes_per_ndim.extend([node] for node in large_pointwise)

        nodes_per_ndim.extend(
            g for g in (not_reduction, short_reduction, long_reduction) if g
        )

    assert sum(len(p) for p in nodes_per_ndim) == len(nodes)
    return nodes_per_ndim