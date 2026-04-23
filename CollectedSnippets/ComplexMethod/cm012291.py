def fuse_matmul_reduce_scatter(reduce_scatter: _ReduceScatterMatch) -> None:
    """
    Fused the pattern

        reduce_scatter_tensor(A @ B, scatter_dim, group_name)

    into

        torch.ops.symm_mem.fused_matmul_reduce_scatter(
            A, B, scatter_dim, group_name,
        )

    Returns boolean indicating if fusion was successful or not.
    """
    if (
        not torch.distributed.is_available()
        or not torch.distributed.is_nccl_available()
    ):
        return

    from torch.distributed._symmetric_memory import (
        is_symm_mem_enabled_for_group,
        restride_A_for_fused_matmul_reduce_scatter,
    )

    (
        input_node,
        _reduce_scatter_node,
        rs_wait_tensor_node,
        reduce_op,
        orig_scatter_dim,
        group_name,
    ) = (
        reduce_scatter.input_node,
        reduce_scatter.reduce_scatter_node,
        reduce_scatter.wait_tensor_node,
        reduce_scatter.reduce_op,
        reduce_scatter.scatter_dim,
        reduce_scatter.group_name,
    )

    if not is_symm_mem_enabled_for_group(group_name):
        return

    filter_matmul = None
    if _is_last_dim(_get_tensor(input_node), orig_scatter_dim):
        # scaled_mm is not supported yet for last dim mm+rs
        def _filter_out_scaled_matmul(matmul: _Matmul):
            return not isinstance(matmul, _ScaledMatmul)

        filter_matmul = _filter_out_scaled_matmul

    # Currently fused_matmul_reduce_scatter doesn't return the matmul result,
    # so we can't apply the fusion if the matmul result is used by multiple
    # users. This is not a fundamental limitation of the fused op and can be
    # addressed if needed.
    if len(input_node.users) != 1:
        log.warning(
            "matmul result has more than one user, skipping fused_matmul_reduce_scatter fusion."
        )
        return

    matmul = _find_producer_matmul(input_node)

    if matmul is None:
        log.warning(
            "no producer matmul found for reduce scatter, skipping fuse_matmul_reduce_scatter fusion"
        )
        return

    if filter_matmul and not filter_matmul(matmul):
        return

    if rs_wait_tensor_node in matmul.arg_ancestor_nodes:
        log.warning(
            "reduce-scatter result node is an ancestor of matmul, skipping fuse_matmul_reduce_scatter fusion"
        )
        return

    # We need to track 3 values for the fused scaled mm reduce scatter implementation:
    #   1. The scatter dim before the reshape, which was assigned using the original (a,b,c) @ (c,d) = (a,b,d) dims.
    #   2. The scatter dim after the reshape, to use when we are doing the 2D (a*b,c) @ (c,d) = (a,b,d) scaled mm op.
    #   3. Store expected potentially 3D+ mm output shape, so we can reshape the 2D mm output to the intended
    #      3D+ shape before applying reduce-scatter, and to prevent shape errors with subsequent ops.

    # If 'A' was reshaped from 3D+ -> 2D for the mm, we need to determine the new scattter dim after the reshape
    # for the fused matmul reduce scatter implementation to use.
    if matmul.pre_mm_reshape:
        scatter_dim_after_maybe_reshape = _scatter_dim_after_reshape(
            matmul.pre_mm_reshape, orig_scatter_dim
        )
    else:
        scatter_dim_after_maybe_reshape = orig_scatter_dim

    # If the 2D mm output was reshaped from 2D -> 3D+, we need to store the intended output shape for the
    # fused matmul reduce scatter implementation to use.
    if matmul.post_mm_reshape:
        output_shape = list(_get_tensor(matmul.post_mm_reshape).shape)
    else:
        A_orig_shape = list(_get_tensor(matmul.A_node).shape)
        B_shape = list(_get_tensor(matmul.B_node).shape)
        output_shape = [*A_orig_shape[:-1], B_shape[-1]]

    graph = rs_wait_tensor_node.graph
    with graph.inserting_before(rs_wait_tensor_node):
        # Restride A tensor before fused op, for optimal perf in fused matmul reduce scatter
        if "val" in matmul.A_node.meta:
            restrided = restride_A_for_fused_matmul_reduce_scatter(
                _get_tensor(matmul.A_node),
                scatter_dim_after_maybe_reshape,
            )
            matmul.A_node = graph.call_function(
                inductor_prims.force_stride_order,
                args=(matmul.A_node, restrided.stride()),
            )

        # Replace matched subgraph with fused matmul reduce scatter node
        fused_node = _insert_fused_matmul_reduce_scatter(
            graph,
            matmul,
            reduce_op,
            orig_scatter_dim,
            group_name,
            scatter_dim_after_maybe_reshape,
            output_shape,
        )
        reduce_scatter.replace_with(fused_node)
        reduce_scatter.erase()
        matmul.erase()

    order = {node: idx for idx, node in enumerate(graph.nodes)}
    nodes_to_raise = sorted(
        matmul.arg_ancestor_nodes,
        key=lambda x: order[x],
    )
    for node in nodes_to_raise:
        if order[node] > order[fused_node]:
            fused_node.prepend(node)

    log.debug("successfully fused matmul reduce scatter")