def _check_input_sizes(n, computation_op):
            # Check if the tensor shape of the 'other' node is the same as or
            # can be broadcasted to the tensor shape of the computation node.
            computation_node = (
                n.args[0] if n.args[1] is match.kwargs["other"] else n.args[1]
            )
            assert computation_node.target == computation_op
            computation_node_size = get_meta_value(computation_node).size()
            if computation_op is mkldnn._linear_pointwise.default:
                broadcast_sizes = []
                if len(computation_node_size) >= 2:
                    broadcast_sizes = [
                        torch.Size(
                            [1 for _ in range(len(computation_node_size) - 1)]
                            + [computation_node_size[-1]]
                        ),
                    ]
            else:
                assert len(computation_node_size) > 2
                broadcast_sizes = [
                    torch.Size(
                        [computation_node_size[0], computation_node_size[1]]
                        + [1 for _ in range(len(computation_node_size) - 2)]
                    ),
                    torch.Size(
                        [1, computation_node_size[1]]
                        + [1 for _ in range(len(computation_node_size) - 2)]
                    ),
                    torch.Size([1 for _ in range(len(computation_node_size))]),
                ]
            return (
                get_meta_value(match.kwargs["other"]).size()
                in [
                    computation_node_size,
                ]
                + broadcast_sizes
            )