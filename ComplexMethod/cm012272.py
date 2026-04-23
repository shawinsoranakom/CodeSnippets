def grouped_gemm_pass(graph: torch.fx.Graph):
        """
        Group GEMM has multi output nodes which is complicated to define a Pattern.
        Use below way to connect the pattern to the lowering.
        TODO: Use MultiOutputPattern, current limitation is the pattern requires
        fixed number of output nodes. Extend to support Group GEMM for pattern matcher.
        """
        computation_op = mkldnn._linear_pointwise.default
        from ..mkldnn_lowerings import grouped_gemm_lowering

        for node in graph.find_nodes(op="call_function", target=computation_op):
            if (
                not node._erased
                and isinstance(node.meta.get("val"), torch.Tensor)
                and node.meta["val"].device.type == "cpu"
            ):
                act = node.args[0]
                users = list(act.users)
                if _is_valid_grouped_gemm_fusion(users):
                    with graph.inserting_before(node):
                        grouped_gemm_node = graph.create_node(
                            "call_function",
                            grouped_gemm_lowering,
                            (
                                act,
                                [user.args[1] for user in users],
                                [user.args[2] for user in users],
                            ),
                        )
                        grouped_gemm_node.meta["val"] = [
                            user.meta["val"] for user in users
                        ]
                        with graph.inserting_after(grouped_gemm_node):
                            for gemm_idx, user in enumerate(users):
                                assert user.target == computation_op
                                get_item = graph.create_node(
                                    "call_function",
                                    operator.getitem,
                                    (
                                        grouped_gemm_node,
                                        gemm_idx,
                                    ),
                                )
                                user.replace_all_uses_with(get_item)
                                graph.erase_node(user)
        return