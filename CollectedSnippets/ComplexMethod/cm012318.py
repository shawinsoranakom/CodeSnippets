def _is_valid_concat_linear_woq_int4_fusion(computation_nodes):
    computation_op = torch.ops.aten._weight_int4pack_mm_for_cpu.default
    act = computation_nodes[0].args[0]
    wgt = computation_nodes[0].args[1]
    in_feature_size = wgt.meta.get("val").size(1)  # type: ignore[union-attr]
    group_size = computation_nodes[0].args[2]
    return len(computation_nodes) >= 2 and all(
        (
            node.target == computation_op
            and node.args[0] == act  # share same activation
            and (
                node.args[1].meta.get("val").size(1) == in_feature_size
            )  # same in feature size
            and (node.args[1] != wgt or gemm_idx == 0)
            and node.args[1].op == "get_attr"  # wgt are all constants
            and node.args[2] == group_size  # same group size
        )
        for gemm_idx, node in enumerate(computation_nodes)
    )