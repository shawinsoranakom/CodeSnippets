def convert_prim_Loop(self, node: torch._C.Node):
        inputs = list(node.inputs())
        self._check_prim_loop_support(node)

        num_iterations = self.get_fx_value_by_ir_value(inputs[0])

        # Find inputs.
        loop_local_arguments = [inp.debugName() for inp in inputs[2:]]

        global_arguments = self._identify_inputs_as_arguments(node)

        # Lift parameters as inputs.
        for block in node.blocks():
            global_arguments = global_arguments.union(
                self.blocks_to_lifted_attrs[block]
            )

        global_arguments = list(global_arguments)

        subgraph_nodes, subgraph_converters = self._convert_block_to_subgraph(
            node, global_arguments
        )

        if len(subgraph_nodes) != 1:
            raise AssertionError(f"expected 1 subgraph node, got {len(subgraph_nodes)}")
        subgraph_converter = subgraph_converters[0]
        if not self.is_top_level_graph():
            self.name_update_from_subblock_to_parent = (
                self.name_update_from_subblock_to_parent.union(
                    subgraph_converter.name_update_from_subblock_to_parent
                )
            )

        fx_block_args = [
            self.get_fx_value_by_fqn(name)
            for name in loop_local_arguments + global_arguments
        ]
        for iter_idx in range(num_iterations):
            loop_node = self.fx_graph.call_function(
                execute_subgraph_from_prim_loop,
                # Check execute_node function for the expected arguments order.
                (
                    subgraph_nodes[0],
                    iter_idx,
                    len(loop_local_arguments),
                    *fx_block_args,
                ),
                {},
            )

            # Update the value of loop local variables.
            if node.outputsSize() >= 1:
                for i, outp in enumerate(node.outputs()):
                    output_name = outp.debugName()
                    self.name_to_node[output_name] = self.fx_graph.call_function(
                        operator.getitem,
                        (
                            loop_node,
                            i + 1,
                        ),  # + 1 because the 0th element is the condition.
                    )
                    fx_block_args[i] = self.name_to_node[output_name]

            # Update the value of global variables, whose values are modified inplace.

            for i, name in enumerate(
                subgraph_converter.name_update_from_subblock_to_parent
            ):
                self.name_to_node[name] = self.fx_graph.call_function(
                    operator.getitem,
                    (
                        loop_node,
                        i + node.outputsSize() + 1,
                    ),  # + 1 because the 0th element is the condition.
                )
                global_argument_index = global_arguments.index(name)
                fx_block_args[i + node.outputsSize() + global_argument_index] = (
                    self.name_to_node[name]
                )