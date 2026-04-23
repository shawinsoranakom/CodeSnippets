def create(
        cls,
        predicate: TensorBox,
        true_fn: Subgraph,
        false_fn: Subgraph,
        operands: list[TensorBox],
    ) -> list[MultiOutput]:
        """Create a Sequence of IRNodes from a conditional statement (see .lowering.cond)"""
        # pyrefly: ignore [bad-assignment]
        predicate = cls.realize_input(predicate)
        # pyrefly: ignore [bad-assignment]
        operands = [cls.realize_input(x) for x in operands]
        fx_operands: Argument = V.graph.current_node.args[-1]

        assert isinstance(fx_operands, Sequence), type(fx_operands)
        # Build fake_operands from FX nodes' metadata
        # For FX Nodes, get the fake tensor from meta["val"]
        # For non-Nodes (e.g., symbolic integers from sym_size lowering), pass directly
        fake_operands: list[Any] = []
        for fx_op in fx_operands:
            if isinstance(fx_op, Node):
                fake_operands.append(fx_op.meta["val"])
            else:
                # Symbolic integer or constant - pass directly
                fake_operands.append(fx_op)
        fake_outputs = V.graph.current_node.meta["val"]

        def _require_exact_strides(
            graph_outputs: Sequence[IRNode],
            fake_tensors: Sequence[torch.Tensor],
        ) -> list[IRNode]:
            ret = []
            for output, fake in zip(graph_outputs, fake_tensors):
                if isinstance(output, ShapeAsConstantBuffer):
                    ret.append(output)
                else:
                    ret.append(
                        # pyrefly: ignore [bad-argument-type]
                        ExternKernel.require_exact_strides(
                            TensorBox(output), fake.stride(), allow_padding=False
                        )
                    )
            # pyrefly: ignore [bad-return]
            return ret

        for subgraph in (true_fn, false_fn):
            if subgraph.graph is None:
                # create and lower subgraphs
                subgraph.graph = V.graph.make_subgraph(
                    gm=subgraph.graph_module,
                    example_inputs=fake_operands,
                    subgraph_name=subgraph.name,
                )
                with V.set_graph_handler(subgraph.graph):
                    subgraph.graph.run(*fake_operands)
                    # Force subgraph outputs to have the expected strides from
                    # FakeTensor metadata. This ensures both branches produce
                    # outputs with consistent strides.
                    subgraph.graph.graph_outputs = _require_exact_strides(
                        subgraph.graph.graph_outputs, fake_outputs
                    )

        assert true_fn.graph is not None
        assert false_fn.graph is not None
        true_outputs = true_fn.graph.graph_outputs
        false_outputs = false_fn.graph.graph_outputs

        for name, outputs in (("true_fn", true_outputs), ("false_fn", false_outputs)):
            if _has_aliased_buffers(true_outputs):
                raise AssertionError(
                    "Output aliasing is currently not supported in compiled torch.cond. "
                    f"The outputs of the {name} subgraph of torch.cond are aliased: {outputs}"
                )

        # make sure true and false outputs are structurally equivalent
        assert len(true_outputs) == len(false_outputs), (true_outputs, false_outputs)
        for i, (t_o, f_o) in enumerate(zip(true_outputs, false_outputs)):
            assert t_o.get_device() == f_o.get_device(), (i, t_o, f_o)
            assert t_o.get_dtype() == f_o.get_dtype(), (i, t_o, f_o)
            assert t_o.get_layout().offset == f_o.get_layout().offset, (i, t_o, f_o)

        # Determine device from operands and predicate
        # The predicate can be on a different device (e.g., CPU for control flow)
        # while the data operands and outputs should be on the compute device, so
        # using predicate device as a fallback.
        device = next(
            o.get_device()
            for o in operands + [predicate]
            if not isinstance(o, ShapeAsConstantBuffer)
        )
        unbacked_bindings = resolve_unbacked_bindings(
            V.graph.sizevars.shape_env,
            V.graph.current_node.meta.get("unbacked_bindings", None),
        )
        assert device is not None, "cannot determine device"
        conditional = Conditional(
            predicate=predicate,
            operands=operands,
            true_subgraph=true_fn,
            false_subgraph=false_fn,
            layout=MultiOutputLayout(device=device),
            unbacked_bindings=unbacked_bindings,
        )

        outputs = [
            MultiOutput(
                FixedLayout(
                    # pyrefly: ignore [bad-argument-type]
                    device=output.get_device()
                    if output.get_device() is not None
                    else device,  # type: ignore[arg-type]
                    dtype=output.get_dtype(),
                    size=[Conditional._maybe_expr(sz) for sz in merged_output.size()],
                    stride=[
                        Conditional._maybe_expr(sz) for sz in merged_output.stride()
                    ],
                    offset=output.get_layout().offset,
                    is_pinned=output.get_layout().is_pinned,
                ),
                conditional,
                [(list, i)],
            )
            # as the true and false outputs are equivalent,
            # we can use either of them here as a "template"
            for i, (output, merged_output) in enumerate(
                zip(true_outputs, V.graph.current_node.meta["val"])
            )
        ]

        conditional.outputs = outputs  # type: ignore[assignment]

        from torch._higher_order_ops.utils import (
            check_input_alias_and_mutation_return_outputs,
        )

        (_, _, _, true_mutated_inputs, _) = (
            check_input_alias_and_mutation_return_outputs(true_fn.graph_module)
        )
        (_, _, _, false_mutated_inputs, _) = (
            check_input_alias_and_mutation_return_outputs(false_fn.graph_module)
        )

        mutated_operand_indices = OrderedSet(true_mutated_inputs) | OrderedSet(
            false_mutated_inputs
        )

        # Create MutationOutput for each mutated operand (for scheduler dependencies)
        conditional.mutation_outputs = [
            MutationOutput(operands[idx].layout, operands[idx], conditional)  # type: ignore[union-attr]
            for idx in sorted(mutated_operand_indices)
        ]

        return outputs