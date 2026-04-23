def fuse_all_gather_matmul(all_gather: _AllGatherMatch) -> None:
    """
    Fused the pattern

        A = all_gather_tensor(A_shard, gather_dim, group_name)
        C_0 = torch.matmul(A, B_0)
        C_1 = torch.matmul(A, B_1)
        C_2 = torch.matmul(A, B_2)
        ...

    into

        A, Cs = torch.ops.symm_mem.fused_all_gather_matmul(
            A_shard, [B_0, B_1, B_2, ...], gather_dim, group_name,
        )
    """
    if (
        not torch.distributed.is_available()
        or not torch.distributed.is_nccl_available()
    ):
        return

    from torch.distributed._symmetric_memory import (
        is_symm_mem_enabled_for_group,
        restride_A_shard_for_fused_all_gather_matmul,
    )

    shard_node, ag_node, ag_res_node, gather_dim, group_name = (
        all_gather.shard_node,
        all_gather.ag_node,
        all_gather.res_node,
        all_gather.gather_dim,
        all_gather.group_name,
    )

    if not is_symm_mem_enabled_for_group(group_name):
        return

    filter_matmul = None
    if _is_last_dim(_get_tensor(shard_node), gather_dim):
        # Decomposed mms should not be too small
        if _get_tensor(shard_node).shape[-1] < 1024:
            return

        # scaled_mm is not supported yet for last dim
        def _filter_out_scaled_matmul(matmul: _Matmul):
            return not isinstance(matmul, _ScaledMatmul)

        filter_matmul = _filter_out_scaled_matmul

    # Find consumer matmuls
    matmuls = _find_consumer_matmuls(ag_res_node)

    # The matmuls are only fusible if non-A args don't depend on the all-gather
    # result node
    matmuls = [
        matmul
        for matmul in matmuls
        if all_gather.res_node not in matmul.arg_ancestor_nodes
    ]

    if len(matmuls) == 0 or len(OrderedSet(map(type, matmuls))) != 1:
        return

    if _is_last_dim(_get_tensor(shard_node), gather_dim) and len(
        all_gather.res_node.users
    ) > len(matmuls):
        # The result of ag-split-cat is used not only in matmuls.
        # Then it has to be materialized, which can have overhead.
        return

    if filter_matmul and not filter_matmul(matmuls[0]):
        return

    # Fuse the all_gather_tensor with the eligible matmuls
    graph = ag_node.graph
    with graph.inserting_before(ag_node):
        if not _is_last_dim(_get_tensor(shard_node), gather_dim):
            if "val" in shard_node.meta:
                restrided = restride_A_shard_for_fused_all_gather_matmul(
                    _get_tensor(shard_node),
                    gather_dim,
                )
                shard_node = graph.call_function(
                    inductor_prims.force_stride_order,
                    args=(shard_node, restrided.stride()),
                )

        fused_node = _insert_fused_all_gather_matmul(
            graph, matmuls, shard_node, gather_dim, group_name
        )
        new_ag_node = graph.call_function(
            operator.getitem,
            args=(fused_node, 0),
        )
        new_out_nodes = graph.call_function(
            operator.getitem,
            args=(fused_node, 1),
        )
        for idx, matmul in enumerate(matmuls):
            new_out_node = graph.call_function(
                operator.getitem,
                args=(new_out_nodes, idx),
            )
            matmul.replace_with(new_out_node)
            matmul.erase()
        all_gather.replace_with(new_ag_node)
        all_gather.erase()

        # If the new_ag_node has no users, we tell the fused op to not return
        # it. This creates more optimization opportunities.
        if len(new_ag_node.users) == 0:
            graph.erase_node(new_ag_node)
            kwargs = dict(fused_node.kwargs)
            if "return_A" in kwargs:
                kwargs["return_A"] = False
                fused_node.kwargs = kwargs

    # Raise ancestors of non-A args that are topologically ordered between
    # ag_res_node and the matmul above fused_node.
    order = {node: idx for idx, node in enumerate(graph.nodes)}
    nodes_to_raise = sorted(
        OrderedSet(x for matmul in matmuls for x in matmul.arg_ancestor_nodes),
        key=lambda x: order[x],
    )
    for node in nodes_to_raise:
        if order[node] > order[fused_node]:
            fused_node.prepend(node)