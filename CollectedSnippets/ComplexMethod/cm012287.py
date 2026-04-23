def _insert_fused_all_gather_matmul(
    graph: torch.fx.Graph,
    matmuls: list[_Matmul],
    shard_node: torch.fx.Node,
    gather_dim: int,
    group_name: "torch.distributed.distributed_c10d.GroupName",
) -> torch.fx.Node:
    mm_types = OrderedSet(map(type, matmuls))
    assert len(mm_types) == 1
    mm_type = next(iter(mm_types))
    if mm_type == _Matmul:
        B_nodes = [matmul.B_node for matmul in matmuls]
        return graph.call_function(
            torch.ops.symm_mem.fused_all_gather_matmul.default,
            args=(shard_node, B_nodes, gather_dim, group_name),
            kwargs={"return_A": True},
        )
    elif mm_type == _ScaledMatmul:
        scaled_matmuls = cast("list[_ScaledMatmul]", matmuls)
        return graph.call_function(
            torch.ops.symm_mem.fused_all_gather_scaled_matmul.default,
            args=(
                shard_node,
                [matmul.B_node for matmul in scaled_matmuls],
                scaled_matmuls[0].A_scale_node,
                [matmul.B_scale_node for matmul in scaled_matmuls],
                gather_dim,
                group_name,
                [matmul.bias_node for matmul in scaled_matmuls],
                [matmul.result_scale_node for matmul in scaled_matmuls],
                [matmul.out_dtype for matmul in scaled_matmuls],
                [matmul.use_fast_accum for matmul in scaled_matmuls],
            ),
        )
    else:
        raise AssertionError(f"Unexpected matmul match type: {mm_type}")