def create(
        cls, subgraph: Subgraph, *operands: IRNode
    ) -> list[ShapeAsConstantBuffer | NoneAsConstantBuffer | MultiOutput]:
        """For each operand, get a realized input, force it to have the same
        strides as the subgraph inputs, then use an InvokeSubgraph"""
        from .lowering import constrain_to_fake_tensor

        # TODO(anijain2305) - Support sym expr as operands in future.
        current_node = V.graph.current_node

        fake_operands = None
        if eager_input_vals := current_node.meta.get("eager_input_vals"):
            # eager_input_vals is (args_values, kwargs_values). We need args for invoke_subgraph
            offset = 2
            if current_node.target is torch.ops.higher_order.with_effects:
                # Aruguments eagerly are (token, subgraph, identifier, *operands)
                assert current_node.args[1] is torch.ops.higher_order.invoke_subgraph
                offset = 3
            fake_operands = eager_input_vals[0][offset:]
        else:
            offset = 2
            if current_node.target is torch.ops.higher_order.with_effects:
                # with_effects args: (token, invoke_subgraph, subgraph, identifier, *operands)
                assert current_node.args[1] is torch.ops.higher_order.invoke_subgraph
                offset = 4

            # For the partitioned backward graph, we do not have
            # eager_input_vals. Here, we rely on the recorded example values.
            fx_operands = current_node.args[offset:]
            fake_operands = [x.meta["val"] for x in fx_operands]  # type: ignore[union-attr]

        # Realize the inputs. Also intermediates can have different strides than
        # the inputs of the subgraph. So, force the intermediates to have same
        # strides as that of subgraph inputs.
        # pyrefly: ignore [annotation-mismatch, redefinition]
        operands: list[IRNode] = [cls.realize_input(x) for x in operands]
        new_operands: list[IRNode] = []

        for idx, operand in enumerate(operands):
            if isinstance(
                operand, (ShapeAsConstantBuffer, GeneratorState, OpaqueObjectState)
            ):
                new_operands.append(operand)
            else:
                new_operands.append(
                    constrain_to_fake_tensor(operand, fake_operands[idx])
                )

        # pyrefly: ignore [bad-assignment]
        operands = new_operands

        if subgraph.graph is None:
            # create and lower subgraphs
            subgraph.graph = V.graph.make_subgraph(
                gm=subgraph.graph_module,
                example_inputs=fake_operands,
                subgraph_name=subgraph.name,
            )
            with V.set_graph_handler(subgraph.graph):
                subgraph.graph.run(*fake_operands)

        outputs = subgraph.graph.graph_outputs

        # Find the device - operands could be integers from shapes, so we can't
        # use operands[0]
        device = None
        for operand in operands:
            if not isinstance(operand, ShapeAsConstantBuffer):
                device = operand.get_device()
                break
        assert device is not None
        invoke_subgraph = InvokeSubgraph(
            subgraph=subgraph,
            operands=operands,
            layout=MultiOutputLayout(device=device),
        )

        def create_output(
            output: IRNode, ind: int
        ) -> ShapeAsConstantBuffer | NoneAsConstantBuffer | MultiOutput:
            if isinstance(output, (ShapeAsConstantBuffer, NoneAsConstantBuffer)):
                return output
            else:
                device = output.get_device()
                assert device is not None

                return MultiOutput(
                    FixedLayout(
                        device=device,
                        dtype=output.get_dtype(),
                        size=output.get_size(),
                        stride=output.get_stride(),
                        offset=output.get_layout().offset,
                        is_pinned=output.get_layout().is_pinned,
                    ),
                    invoke_subgraph,  # type: ignore[has-type]
                    [(list, ind)],
                    skip_size_stride_alignment_checks=True,
                )

        outs = [create_output(output, i) for i, output in enumerate(outputs)]
        invoke_subgraph.outputs = outs  # type: ignore[assignment]
        return outs