def create(
        cls,
        cond_fn: Subgraph,
        body_fn: Subgraph,
        carried_inputs: Sequence[IRNode],
        additional_inputs: Sequence[IRNode],
        stack_output: bool,
    ) -> IRNode | Sequence[IRNode]:
        """create the while_loop IR node. stack_output controls whether it stack
        each iterations' output, which is necessary for training.
        """
        from torch._higher_order_ops.utils import check_input_alias_and_mutation

        def _require_exact_strides(
            tensor_boxes: Sequence[IRNode],
            fake_tensors: list[int | torch.SymInt | torch.Tensor],
        ) -> list[IRNode]:
            assert len(tensor_boxes) == len(fake_tensors)
            ret = []
            for tb, fk in zip(tensor_boxes, fake_tensors):
                if isinstance(fk, torch.Tensor):
                    # Subgraph lowering always return StorageBox as graph_outputs because
                    # it realizes the outputs.
                    #
                    # However, require_exact_strides is expecting TensorBox
                    # e.g. in require_exact_strides when an expand happens,
                    # the fake tensor's stride is (0, 0, 0) but the storage
                    # box might have a different stride so lowering.slice_
                    # is used to make the stride consistent and it expects input to
                    # be TensorBox.
                    #
                    # So we wrap the inputs as tensor boxes if they're not yet.
                    new_tb = WhileLoop._maybe_wrap_as_tensor_box(tb)
                    ret.append(
                        ExternKernel.require_exact_strides(
                            new_tb, fk.stride(), allow_padding=False
                        )
                    )
                else:
                    ret.append(tb)
            return ret

        fx_carried_inputs = V.graph.current_node.args[-2]
        fx_additional_inputs = V.graph.current_node.args[-1]
        fx_all_inputs = fx_carried_inputs + fx_additional_inputs  # type: ignore[operator]
        fake_all_inputs = [x.meta["val"] for x in fx_all_inputs]  # type: ignore[union-attr]
        fake_carried_inputs = [x.meta["val"] for x in fx_carried_inputs]  # type: ignore[union-attr]
        fake_additional_inputs = [x.meta["val"] for x in fx_additional_inputs]  # type: ignore[union-attr]

        carried_inputs_ = [cls.realize_input(x) for x in carried_inputs]
        carried_inputs_ = WhileLoop._clone_aliased_inputs(carried_inputs_)
        carried_inputs_ = _require_exact_strides(carried_inputs_, fake_carried_inputs)
        additional_inputs_ = [cls.realize_input(x) for x in additional_inputs]
        additional_inputs_ = _require_exact_strides(
            additional_inputs_, fake_additional_inputs
        )
        all_inputs = carried_inputs_ + additional_inputs_

        for subgraph in (cond_fn, body_fn):
            if subgraph.graph is None:
                # create and lower subgraphs
                assert isinstance(fx_all_inputs, Sequence), type(fx_all_inputs)
                subgraph.graph = V.graph.make_subgraph(
                    gm=subgraph.graph_module,
                    example_inputs=fx_all_inputs,  # type: ignore[arg-type]
                    subgraph_name=subgraph.name,
                )
                with V.set_graph_handler(subgraph.graph):
                    subgraph.graph.run(*fake_all_inputs)
                    # For body_fn, we require its output to have the exact same stride
                    # as inputs because the previous output is the input of next iteration.
                    #
                    # This cannot be automatically done in graph lowering because body_fn's graph outputs
                    # are not user-facing so the special handling for strides of user-facing output in graph
                    # lowering is not applicable.
                    if subgraph is body_fn:
                        assert len(subgraph.graph.graph_outputs) == len(
                            fake_carried_inputs
                        )
                        subgraph.graph.graph_outputs = _require_exact_strides(  # type: ignore[assignment]
                            subgraph.graph.graph_outputs,
                            fake_carried_inputs,
                        )

        assert cond_fn.graph and body_fn.graph
        cond_outputs = cond_fn.graph.graph_outputs
        body_outputs = body_fn.graph.graph_outputs

        if _has_aliased_buffers(body_outputs):
            raise AssertionError(
                "Output aliasing is currently not supported in compiled torch.while_loop. "
                f"The outputs of the body_fn subgraph of torch.while_loop are aliased: {body_outputs}"
            )

        # make sure cond_fn returns a boolean scalar Tensor
        assert len(cond_outputs) == 1, cond_outputs
        p = cond_outputs[0]
        if not isinstance(p, ShapeAsConstantBuffer):
            assert p.get_dtype() == torch.bool, p
            assert len(p.get_size()) == 0, p

        assert len(all_inputs) > 0, (
            "torch.while_loop is assumed to have at least one operand."
        )

        device = all_inputs[0].get_device()

        assert device is not None  # to make linter happy
        # make sure carried_inputs_ and body outputs are structurally equivalent
        assert len(carried_inputs_) == len(body_outputs), (
            carried_inputs_,
            body_outputs,
        )
        for i, (op, bo) in enumerate(zip(carried_inputs_, body_outputs)):

            def _guard_list_equals(
                lhs_exprs: Sequence[int | sympy.Expr],
                rhs_exprs: Sequence[int | sympy.Expr],
            ) -> None:
                assert len(lhs_exprs) == len(rhs_exprs)
                for lhs, rhs in zip(lhs_exprs, rhs_exprs):
                    V.graph.sizevars.check_equals(lhs, rhs)

            _guard_list_equals(op.get_size(), bo.get_size())
            _guard_list_equals(op.get_stride(), bo.get_stride())
            # assume all carried_inputs_ and outputs are on the same device
            # as the MultiOutputLayout below requires single device
            assert op.get_device() == bo.get_device(), (i, op, bo, device)
            assert op.get_dtype() == bo.get_dtype(), (i, op, bo)

        assert device is not None

        unbacked_bindings = resolve_unbacked_bindings(
            V.graph.sizevars.shape_env,
            V.graph.current_node.meta.get("unbacked_bindings", None),
        )

        while_loop = WhileLoop(
            carried_inputs=carried_inputs_,
            additional_inputs=additional_inputs_,
            cond_subgraph=cond_fn,
            body_subgraph=body_fn,
            # asserted above that there is at least one operand
            layout=MultiOutputLayout(device=device),
            unbacked_bindings=unbacked_bindings,
            stack_output=stack_output,
        )

        assert body_fn.graph is not None and isinstance(
            body_fn.graph.module, torch.fx.GraphModule
        )  # to make linter happy

        # Handling input mutations
        mutated_idxs = check_input_alias_and_mutation(
            body_fn.graph.module, fake_all_inputs
        )[3]
        mutated_idx_set = OrderedSet(mutated_idxs)
        mutated_inputs = [all_inputs[idx] for idx in mutated_idx_set]

        # Create all outputs first
        mutated_inputs_iter = iter(mutated_inputs)
        all_outputs: list[IRNode] = []
        while_loop.outputs = []
        while_loop.mutation_outputs = []
        if stack_output:
            assert len(mutated_idx_set) == 0, (
                "NYI: while_loop_stack_output input mutations."
            )
            for idx, output in enumerate(V.graph.current_node.meta["val"]):
                # Create MultiOutput for regular outputs
                multi_out = MultiOutput(
                    FixedLayout(
                        device=output.device,  # type: ignore[arg-type]
                        dtype=output.dtype,
                        size=[Conditional._maybe_expr(sz) for sz in output.size()],
                        stride=[Conditional._maybe_expr(st) for st in output.stride()],
                    ),
                    while_loop,
                    [(list, idx)],
                )
                while_loop.outputs.append(multi_out)
                all_outputs.append(multi_out)
        else:
            for idx, output in enumerate(body_outputs):
                if idx in mutated_idx_set:
                    assert idx < len(carried_inputs), "only carries can be mutated."
                    # Create MutationOutput for mutated inputs
                    mutated_input = next(mutated_inputs_iter)
                    while_loop.mutation_outputs.append(
                        MutationOutput(mutated_input.layout, mutated_input, while_loop)  # type: ignore[attr-defined, union-attr]
                    )
                    all_outputs.append(mutated_input)
                else:
                    multi_out = MultiOutput(
                        FixedLayout(
                            device=output.get_device(),  # type: ignore[arg-type]
                            dtype=output.get_dtype(),
                            size=output.get_size(),
                            stride=output.get_stride(),
                            offset=output.get_layout().offset,
                        ),
                        while_loop,
                        [(list, idx)],
                    )
                    while_loop.outputs.append(multi_out)
                    all_outputs.append(multi_out)

        for inp, out in zip(carried_inputs, all_outputs):
            if inp.get_name() in V.graph.graph_inputs:
                # if a carried input of the while_loop is a graph input,
                # it can be returned as is when the number of iterations
                # is zero. due to this, we can't (generally) reuse the
                # output buffers corresponding to the graph inputs, as
                # the inputs may end up being mutated.
                V.graph.never_reuse_buffers.add(out.get_name())
        return all_outputs