def convert_graph_outputs(self):
        args = []
        outp_name_list = [outp.debugName() for outp in self.ts_graph.outputs()] + list(
            self.name_update_from_subblock_to_parent
        )
        for output_name in outp_name_list:
            if output_name in self.name_to_node:
                fx_node = self.name_to_node[output_name]
                # TODO: Revisit this later after HigherOrderOp design changes.
                # Currently, we cannot directly return input as output.
                if (
                    not self.is_top_level_graph()
                    and isinstance(fx_node, torch.fx.Node)
                    and fx_node.op == "placeholder"
                ):
                    fx_node = self.fx_graph.call_function(torch.clone, (fx_node,))
                args.append(fx_node)
                self.output_specs.append(
                    OutputSpec(
                        OutputKind.USER_OUTPUT,
                        arg=TensorArgument(name=output_name),
                        target=output_name,
                    )
                )
            elif output_name in self.name_to_constant:
                args.append(self.name_to_constant[output_name])
                self.output_specs.append(
                    OutputSpec(
                        OutputKind.USER_OUTPUT,
                        arg=ConstantArgument(
                            name=output_name, value=self.name_to_constant[output_name]
                        ),
                        target=output_name,
                    )
                )
            else:
                raise ValueError(f"Output {output_name} not found")

        if len(args) == 0:
            # Sub-block of prim::If can have zero output.
            self.fx_graph.output([])
        elif len(args) == 1:
            self.fx_graph.output(
                args[0]
            )  # Get rid of an extra list wrapped around final output.
        elif len(args) > 1:
            self.fx_graph.output(
                args
            )  # For prim::Loop and prim::If with multiple outputs.
        else:
            # Sub-block of prim::Loop can have multiple outputs.
            self.fx_graph.output(args)