def convert_prim_If(self, node: torch._C.Node):
        self._check_set_attr_in_if_block(node)

        inputs = list(node.inputs())
        if len(inputs) != 1:
            raise AssertionError(f"expected 1 input for prim::If, got {len(inputs)}")
        predicate = self.get_fx_value_by_ir_value(inputs[0])

        # Find inputs.
        arguments = self._identify_inputs_as_arguments(node)

        # Lift parameters as inputs.
        for block in node.blocks():
            arguments = arguments.union(self.blocks_to_lifted_attrs[block])

        arguments = list(arguments)
        subgraph_nodes, _ = self._convert_block_to_subgraph(node, arguments)

        if len(subgraph_nodes) != 2:
            raise AssertionError(
                f"expected 2 subgraph nodes, got {len(subgraph_nodes)}"
            )

        fx_block_args = [self.get_fx_value_by_fqn(name) for name in arguments]

        args = (
            predicate,
            subgraph_nodes[0],
            subgraph_nodes[1],
            tuple(fx_block_args),
        )

        cond_node = self.fx_graph.call_function(torch.cond, args, {})

        # prim::If can also have zero output.
        if node.outputsSize() == 1:
            output_name = node.output().debugName()
            self.name_to_node[output_name] = cond_node
        elif node.outputsSize() > 1:
            for i, output in enumerate(node.outputs()):
                output_name = output.debugName()
                getitem = self.fx_graph.call_function(operator.getitem, (cond_node, i))
                self.name_to_node[output_name] = getitem