def prune_tensors(input_nodes: list[ir.IRNode], new_input_nodes: list[ir.IRNode]):
    """
    Prune unused tensors from `V.graph` since the GEMM Template use new packed weight.
    """

    def share_storage(base_tensor: torch.Tensor, comp_tensor: torch.Tensor):
        return base_tensor.is_mkldnn == comp_tensor.is_mkldnn and (
            is_same_tensor(base_tensor, comp_tensor)
            or is_same_mkldnn_tensor(base_tensor, comp_tensor)
        )

    def get_candidates(input_nodes, new_input_nodes):
        # Only Constant Buffer like weight and bias might be changed in GEMM Template.
        # The Inductor IR Node may changed, but still share the storage. For example:
        # bias in bfloat16 case which only do the expand
        return [
            node
            for node in input_nodes
            if (
                node not in new_input_nodes
                and isinstance(node, (ir.TensorBox, ir.StorageBox))
                and node.get_name() in V.graph.constants
                and not any(
                    (
                        isinstance(new_node, (ir.TensorBox, ir.StorageBox))
                        and new_node.get_name() in V.graph.constants
                        and share_storage(
                            V.graph.constants[node.get_name()],
                            V.graph.constants[new_node.get_name()],
                        )
                    )
                    for new_node in new_input_nodes
                )
            )
        ]

    for candidate_node in get_candidates(input_nodes, new_input_nodes):
        # By using the new packed weight for the GEMM template, we can prune the
        # old weight if it has no other users. This saves memory but makes the FX graph
        # non-retraceable. To support retracing, we can add a repack node to the
        # FX graph. For example:
        # mkldnn._linear_pointwise <- repack_linear_wgt <- packed_wgt_for_template
        candidate_tensor_users = 0
        candidate_tensor = V.graph.constants[candidate_node.get_name()]
        for node in reversed(V.graph.graph.nodes):
            # Case may happen when the candidate tensor is used by more than 1 get_attr node
            # https://github.com/pytorch/pytorch/issues/134998
            if node.op == "get_attr" and hasattr(
                V.graph.module, node.target
            ):  # candidate tensor might already be deleted
                comp_tensor = getattr(V.graph.module, node.target)
                if isinstance(comp_tensor, torch.Tensor) and share_storage(
                    candidate_tensor, comp_tensor
                ):
                    candidate_tensor_users += 1

        for node in reversed(V.graph.graph.nodes):
            # The get_attr node has only 1 user fx node
            # The candidate tensor has been used by only 1 get_attr node
            if (
                node.op == "get_attr"
                and node.target == candidate_node.get_name()
                and len(node.users) == 1
                and candidate_tensor_users == 1
            ):
                del V.graph.constants[node.target]
                delattr(V.graph.module, node.target)
                delattr(V.graph.graph.owning_module, node.target)
                counters["inductor"]["select_algorithm_weight_prune"] += 1