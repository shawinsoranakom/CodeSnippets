def concat_linear_woq_int4(gm: torch.fx.GraphModule):
    """
    Concat Linear optimization pass for WOQ int4
    This pass fuses the original pattern:
    def ...
        return (woq_int4(x, w1, group_size, scale_zp1), woq_int4(x, w2, group_size, scale_zp1) ...)
    into a single operation:
    def ...
        concat_res = woq_int4(x, concat_w, group_size, concat_scale_zp)
        return split(concat_res, split_size_list)
    """

    def concat_wgt(packed_wgts, scale_zps, group_size, act_dtype):
        # Concat the wgts and scale_zps, and repack the wgt
        unpacked_wgts = []
        for packed_wgt in packed_wgts:
            # Get the unpacked weight list
            # Same as https://github.com/pytorch/pytorch/pull/156174
            K = packed_wgt.size(1) * 2
            N = packed_wgt.size(0)
            x = torch.eye(K).to(dtype=act_dtype)
            qscales_and_zeros = (
                torch.tensor([1.0, 8.0])
                .to(dtype=act_dtype)
                .expand(K // group_size, N, 2)
                .contiguous()
            )
            unpacked_wgts.append(
                torch.ops.aten._weight_int4pack_mm_for_cpu(
                    x,
                    packed_wgt,
                    group_size,
                    qscales_and_zeros,
                )
                .t()
                .contiguous()
                .to(torch.int32)  # N, K
            )
        concat_unpacked_wgt = torch.cat(unpacked_wgts, dim=0)
        repack_w = torch.ops.aten._convert_weight_to_int4pack_for_cpu(
            concat_unpacked_wgt, 1
        )
        concat_scale_zp = torch.cat(scale_zps, dim=1).contiguous()
        return repack_w, concat_scale_zp

    graph = gm.graph
    computation_op = torch.ops.aten._weight_int4pack_mm_for_cpu.default
    for node in graph.find_nodes(op="call_function", target=computation_op):
        if (
            not node._erased
            and isinstance(node.meta.get("val"), torch.Tensor)
            and node.meta["val"].device.type == "cpu"
        ):
            act = node.args[0]
            users = list(act.users)
            if _is_valid_concat_linear_woq_int4_fusion(users):
                with graph.inserting_before(node):
                    assert all(user.args[1].op == "get_attr" for user in users)
                    computation_node_0 = users[0]
                    packed_wgts = [getattr(gm, user.args[1].target) for user in users]
                    group_size = computation_node_0.args[2]
                    scale_zps = [getattr(gm, user.args[3].target) for user in users]
                    out_feature_size_list = [
                        packed_wgt.size(0) for packed_wgt in packed_wgts
                    ]
                    repack_w, concat_scale_zp = concat_wgt(
                        packed_wgts, scale_zps, group_size, act.meta.get("val").dtype
                    )
                    repack_w_node_name = computation_node_0.args[1].target + "_concat"
                    concat_scale_zp_node_name = (
                        computation_node_0.args[3].target + "_concat"
                    )
                    gm.register_buffer(repack_w_node_name, repack_w)
                    setattr(gm, repack_w_node_name, repack_w)
                    gm.register_buffer(concat_scale_zp_node_name, concat_scale_zp)
                    setattr(gm, concat_scale_zp_node_name, concat_scale_zp)

                    repack_w_node = graph.create_node(
                        "get_attr", repack_w_node_name, (), {}
                    )
                    with graph.inserting_after(repack_w_node):
                        concat_scale_zp_node = graph.create_node(
                            "get_attr", concat_scale_zp_node_name, (), {}
                        )

                    with graph.inserting_after(concat_scale_zp_node):
                        concat_int4_gemm_node = graph.create_node(
                            "call_function",
                            computation_op,
                            (
                                act,
                                repack_w_node,
                                group_size,
                                concat_scale_zp_node,
                            ),
                        )
                    with graph.inserting_after(concat_int4_gemm_node):
                        split_node = graph.create_node(
                            "call_function",
                            torch.ops.aten.split_with_sizes.default,
                            (
                                concat_int4_gemm_node,
                                out_feature_size_list,
                                1,  # split dim
                            ),
                        )
                    with graph.inserting_after(split_node):
                        for gemm_idx, user in enumerate(users):
                            assert user.target == computation_op
                            get_item = graph.create_node(
                                "call_function",
                                operator.getitem,
                                (
                                    split_node,
                                    gemm_idx,
                                ),
                            )
                            with graph.inserting_after(get_item):
                                clone_node = graph.create_node(
                                    "call_function",
                                    torch.ops.aten.clone.default,
                                    (get_item,),
                                    {"memory_format": torch.contiguous_format},
                                )
                                user.replace_all_uses_with(clone_node)
                                graph.erase_node(user)