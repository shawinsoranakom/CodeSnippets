def placeholder(
        self,
        target: str,  # type: ignore[override]
        args: tuple[object],  # type: ignore[override]
        kwargs: dict[str, object],
    ) -> Expr | TensorBox | None:
        self.placeholder_idx += 1
        example = super().placeholder(target, args, kwargs)  # type: ignore[arg-type]
        target = self.qualify_name(target)
        if isinstance(example, SymTypes):
            # TODO fix partitioning issue and re-enable for backward
            # https://github.com/pytorch/pytorch/issues/155468.
            if not V.graph.is_backward:
                expr = _get_placeholder_expr(example.node)
            else:
                expr = example.node.expr
            self.graph_inputs[target] = expr
            self.graph_input_names.append(target)
            return expr
        elif isinstance(example, (int, bool, float)):
            expr = sympy.sympify(example)
            self.graph_inputs[target] = expr
            self.graph_input_names.append(target)
            return expr
        elif isinstance(example, FakeScriptObject):
            obj = TorchBindObject(name=target, value=example)
            self.graph_inputs[target] = obj
            self.graph_input_names.append(target)
            return obj
        elif example is None:
            self.graph_input_names.append(target)
            return None
        if isinstance(example, BackwardState):
            # Ignored arg, must be unused
            # Alternately we could filter this out in AotAutograd
            self.graph_input_names.append(target)
            return None
        # See note: Note: [Generator arguments in AOTDispatcher]
        elif isinstance(example, torch.Generator):
            assert len(V.graph.current_node.users) == 1 and next(
                iter(V.graph.current_node.users)
            ).target in (
                torch._prims.rng_prims.graphsafe_run_with_rng_state,
                torch.ops.higher_order.invoke_subgraph,
            )
            gen = ir.GeneratorState(name=target, device=example.device)
            self.graph_inputs[target] = gen  # type: ignore[assignment]
            self.graph_input_names.append(target)
            return gen
        elif is_opaque_reference_type(type(example)):
            opaque_obj = ir.OpaqueObjectState(name=target, value=example)
            self.graph_inputs[target] = opaque_obj  # type: ignore[assignment]
            self.graph_input_names.append(target)
            return opaque_obj

        assert isinstance(example, torch.Tensor), example
        # todo(chilli): We can remove the last check once we turn buffers into
        # static shape tensors. That's a hack to workaround Inductor believing
        # the buffer should be static but us passing in a fake tensor with
        # symbolic shapes.
        if not example._has_symbolic_sizes_strides:
            # the first N inputs are weights
            sizes, strides = self.static_sizes_strides(example)
        else:
            sizes, strides = self.symbolic_sizes_strides(example)  # type: ignore[assignment]

        if (
            self.is_backward
            and self.bw_donated_idxs
            and self.placeholder_idx in self.bw_donated_idxs
        ):
            tensor = TensorBox.create(
                DonatedBuffer(
                    name=target,
                    layout=FixedLayout(example.device, example.dtype, sizes, strides),
                )
            )
        else:
            # TODO(jansel): handle input aliasing
            tensor = TensorBox.create(
                InputBuffer(
                    name=target,
                    layout=FixedLayout(example.device, example.dtype, sizes, strides),
                )
            )

        self.graph_inputs[target] = tensor
        self.graph_input_names.append(target)
        self.graph_inputs_original[target] = tensor.data.data  # type: ignore[union-attr]
        if self.current_node.users:  # cudagraphs should work with an unused CPU input
            self.add_device_info(example.device)

        # Note: [Input Alignment handling in Inductor]
        # Alignment matters for generating efficient code. Some operations,
        # e.g. vectorized loads, can only be performed on aligned inputs.
        #
        # But if we codegen assuming aligned inputs and then get unaligned
        # inputs at runtime, then we are forced to clone - which is bad for
        # both perf and memory usage.
        #
        # One option would be to guard on storage_offset%ALIGNMENT, and then
        # codegen based on this. But storage_offset guards turned out to be
        # expensive and cause recompiles; Instead, we're generating code
        # based on the alignment of the example input without guarding.
        with maybe_get_suppress_shape_guards_ctx():
            if not should_assume_input_aligned(example):
                self.unaligned_buffers.add(target)
        return tensor