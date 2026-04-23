def _pad_strides(
        in_strides: Sequence[int], size: Sequence[Expr], dtype: torch.dtype
    ) -> Sequence[int]:
        """
        The padding does not change stride order but makes sure all strides larger
        than the threshold are multiple of align.
        """
        align = get_align_for_dtype(dtype)
        if len(in_strides) == 0:
            return in_strides

        if not config.pad_channels_last and Layout.is_channels_last_contiguous(
            size, in_strides
        ):
            return in_strides

        current_fx_node = V.get_current_node()
        if hasattr(current_fx_node, "meta") and current_fx_node.meta.get(
            "dislike_padding", False
        ):
            return in_strides

        # Skip padding the strides for dynamic shapes based on config.pad_dynamic_shape
        # Checking both shape and strides, as there are cases where only one is dynamic
        is_dynamic = not all(
            isinstance(s, (int, sympy.Integer))
            for s in itertools.chain(in_strides, size)
        )
        if not config.pad_dynamic_shapes and is_dynamic:
            return in_strides

        shape_env = V.graph._shape_env if hasattr(V.graph, "_shape_env") else None

        def contains_unbacked_symints(expr: sympy.Expr | int) -> bool:
            if shape_env is None:
                return False
            if not isinstance(expr, sympy.Expr):
                return False
            return any(shape_env.is_unbacked_symint(s) for s in expr.free_symbols)

        # Skip padding the strides when it contains unbacked symints for now.
        if shape_env and any(contains_unbacked_symints(s) for s in in_strides):
            return in_strides

        stride_order = get_stride_order(in_strides, shape_env)
        fill_order = stride_order2fill_order(stride_order)

        new_strides = [0 for _ in range(len(in_strides))]
        # since we pad when the layout is flexible, we can decide the
        # smallest stride to be 1.
        new_strides[fill_order[0]] = 1

        padded = False
        for rank, idx in enumerate(fill_order[1:], start=1):
            prev_idx = fill_order[rank - 1]
            stride = new_strides[prev_idx] * size[prev_idx]
            # Static stride and meets padding conditions OR
            # Dynamic stride and config.pad_dynamic_shape=True
            require_padding = (
                isinstance(stride, (int, sympy.Integer))
                and stride > config.padding_stride_threshold
                and stride % align != 0
            ) or (isinstance(stride, sympy.Expr) and config.pad_dynamic_shapes)
            new_strides[idx] = stride
            if require_padding:
                new_strides[idx] = ceildiv(stride, align) * align
                padded = True

        if not padded:
            # Consider a tensor with shape [256, 1, 5, 5]
            # Avoid strides like [25, 5, 5, 1] being padded to equivalent strides
            # [25, 25, 5, 1].
            return in_strides

        # pyrefly: ignore [bad-assignment]
        metrics.num_comprehensive_padding += 1
        return new_strides