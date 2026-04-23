def _get_updated_graph_signature(
            old_signature: ExportGraphSignature,
            new_gm: torch.fx.GraphModule,
        ) -> ExportGraphSignature:
            """
            Update the graph signature's user_input/user_outputs.
            """
            new_input_specs = []
            for i, node in enumerate(new_gm.graph.nodes):
                if node.op != "placeholder":
                    break

                if i >= len(old_signature.input_specs):
                    raise AssertionError(
                        f"Number of inputs changed after transformation: got index {i} "
                        f"but only {len(old_signature.input_specs)} input_specs"
                    )
                old_input_spec = old_signature.input_specs[i]
                arg = (
                    old_input_spec.arg
                    if isinstance(
                        old_input_spec.arg, (ConstantArgument, CustomObjArgument)
                    )
                    else type(old_input_spec.arg)(node.name)
                )
                new_input_specs.append(
                    InputSpec(
                        old_input_spec.kind,
                        arg,
                        old_input_spec.target,
                        old_input_spec.persistent,
                    )
                )

            output_node = list(new_gm.graph.nodes)[-1]
            if output_node.op != "output":
                raise AssertionError(
                    f"expected last node to have op='output', got {output_node.op!r}"
                )

            new_output_specs = []
            for i, node in enumerate(output_node.args[0]):
                if i >= len(old_signature.output_specs):
                    raise AssertionError(
                        f"Number of outputs changed after transformation: got index {i} "
                        f"but only {len(old_signature.output_specs)} output_specs"
                    )
                old_output_spec = old_signature.output_specs[i]
                arg = (
                    old_output_spec.arg
                    if isinstance(
                        old_output_spec.arg, (ConstantArgument, CustomObjArgument)
                    )
                    else type(old_output_spec.arg)(node.name)
                )
                new_output_specs.append(
                    OutputSpec(old_output_spec.kind, arg, old_output_spec.target)
                )

            new_signature = ExportGraphSignature(
                input_specs=new_input_specs, output_specs=new_output_specs
            )
            return new_signature