def create(cls, x: IRNode, new_size: Sequence[Expr]) -> IRNode:  # type: ignore[override]
        assert isinstance(new_size, Sequence), type(new_size)
        old_size, new_size = cls.resolve_negative_size(x.get_size(), new_size)

        # Skip pointless views
        if V.graph.sizevars.statically_known_list_equals(old_size, new_size):
            return x

        unbacked_symbols_in_sizes = (
            len(free_unbacked_symbols(old_size)) > 0
            or len(free_unbacked_symbols(new_size)) > 0
        )
        is_contiguous = is_dense_contiguous_storage_and_layout(x)

        def create_reinterpret_view(
            inp: IRNode, new_size: Sequence[Expr], new_stride: Sequence[Expr]
        ) -> ReinterpretView:
            inp = ExternKernel.require_exact_strides(
                inp, FlexibleLayout.contiguous_strides(inp.get_size())
            )
            storage, old_layout = as_storage_and_layout(inp)
            new_layout = FixedLayout(
                old_layout.device,
                old_layout.dtype,
                new_size,
                new_stride,
                old_layout.offset,
                old_layout.is_pinned,
            )
            return ReinterpretView(data=storage, layout=new_layout)

        def handle_unbacked_or_dynamic_reshape(
            x: IRNode,
        ) -> IRNode:
            """
            Handle the case where view is not possible with current strides.
            Try dynamic_reshape_indexer first; if it fails with unbacked
            symbols (guard_or_false can't resolve comparisons), fall back
            to making the tensor contiguous.
            """
            nonlocal old_size, new_size
            try:
                reindex = cls.dynamic_reshape_indexer(old_size, new_size)
                return cls(data=x, size=list(new_size), reindex=reindex)
            except GuardOnDataDependentSymNode:
                # dynamic_reshape_indexer cannot handle unbacked SymInts
                # because guard_or_false can't resolve size comparisons.
                # https://github.com/pytorch/pytorch/issues/145561
                x = ExternKernel.require_contiguous(x)
                return create_reinterpret_view(
                    x, new_size, FlexibleLayout.contiguous_strides(new_size)
                )

        if 0 in new_size:

            def fake_reindex(index: Any) -> tuple[int, ...]:
                return tuple([0] * len(old_size))

            return cls(data=x, size=list(new_size), reindex=fake_reindex)

        # TODO: a new class for FixedTransferLayout that output layout is constrained by input layout
        elif is_contiguous:
            # Input is contiguous, output can use contiguous strides
            return create_reinterpret_view(
                x, new_size, FlexibleLayout.contiguous_strides(new_size)
            )

        # Input is non-contiguous. Check if we can get storage/layout.
        if not is_storage_and_layout(x):
            # Can't get storage/layout (e.g., for Pointwise nodes)
            return handle_unbacked_or_dynamic_reshape(x)

        # Try to compute valid output strides.
        storage, old_layout = as_storage_and_layout(x, freeze=False)

        old_stride = old_layout.stride

        # Convert sympy exprs to SymInt for _compute_stride, then convert back
        old_size_symint = V.graph.sizevars.to_symints_or_ints(old_size)
        old_stride_symint = V.graph.sizevars.to_symints_or_ints(old_stride)
        new_size_symint = V.graph.sizevars.to_symints_or_ints(new_size)

        from torch._subclasses.fake_impls import _compute_stride

        # Use size_oblivious=True for unbacked symbols to avoid DDE errors
        new_stride_symint = _compute_stride(
            old_size_symint,
            old_stride_symint,
            new_size_symint,
            size_oblivious=unbacked_symbols_in_sizes,
        )

        if new_stride_symint is not None:
            # Convert SymInt back to sympy expressions
            new_stride = [
                s.node.expr if hasattr(s, "node") else sympy.Integer(s)
                for s in new_stride_symint
            ]
            # View is possible with computed strides
            new_layout = FixedLayout(
                old_layout.device,
                old_layout.dtype,
                new_size,
                new_stride,
                old_layout.offset,
                old_layout.is_pinned,
            )
            return ReinterpretView(data=storage, layout=new_layout)

        # View not possible with current strides
        return handle_unbacked_or_dynamic_reshape(x)