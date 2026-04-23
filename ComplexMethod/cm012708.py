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