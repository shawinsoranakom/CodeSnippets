def folded_op(match, *args, **kwargs):
            counters["inductor"]["binary_folding"] += 1
            other = kwargs.get("other")
            binary_node = match.output_node()
            reshape_node = None
            if binary_node.args[0].target in _computation_ops:
                computation_node = binary_node.args[0]
            elif binary_node.args[0].target is aten.reshape.default:
                computation_node = binary_node.args[0].args[0]
                reshape_node = binary_node.args[0]
            elif binary_node.args[1].target in _computation_ops:
                computation_node = binary_node.args[1]
            else:
                computation_node = binary_node.args[1].args[0]
                reshape_node = binary_node.args[1]
            graph = match.graph
            with graph.inserting_before(reshape_node if reshape_node else binary_node):
                assert computation_node.target in _computation_ops
                if computation_node.target is aten.convolution.default:
                    counters["inductor"]["binary_folding_conv"] += 1
                    new_computation_node = _create_new_conv_node(
                        graph, computation_node, binary_node, other
                    )
                else:
                    new_computation_node = _create_new_linear_node(
                        graph, computation_node, binary_node, other
                    )
                new_computation_node.meta.update(computation_node.meta)
                if reshape_node:
                    assert reshape_node.target is aten.reshape.default
                    computation_node.replace_all_uses_with(new_computation_node)
                    binary_node.replace_all_uses_with(reshape_node)
                else:
                    binary_node.replace_all_uses_with(new_computation_node)
                graph.erase_node(binary_node)
                graph.erase_node(computation_node)