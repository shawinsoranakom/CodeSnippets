def apply_constraint(idx, arg, fx_arg):
        if not _is_tensor_irnode(arg):
            return arg

        meta_val = fx_arg.meta["val"]
        meta_stride_expr = [
            s.node.expr if isinstance(s, torch.SymInt) else s for s in meta_val.stride()
        ]
        shape_env = V.graph.sizevars.shape_env
        stride_order = ir.get_stride_order(meta_val.stride(), shape_env)

        if stride_order and stride_order[-1] != 0:
            # contiguous stride order
            stride_order = list(reversed(range(len(arg.get_size()))))

        if (
            fx_node.target
            == aten._scaled_dot_product_efficient_attention_backward.default
            and idx in (0, 5)
        ):
            assert len(stride_order) == 4
            # The 0 and 5th arguments for aten._scaled_dot_product_efficient_attention_backward.default
            # are for out and gradient_out. They have to be in
            # (3, 1, 2, 0) stride order. Otherwise the kernel will crash.
            # Check https://github.com/pytorch/pytorch/issues/138772
            stride_order = (3, 1, 2, 0)

        # Cache keyed by (id(arg), arg_name, stride_order) to avoid
        # duplicate copy_input when the same tensor feeds multiple SDPA
        # positions (e.g., key=value).  Including arg_name handles
        # mutation: mark_buffer_mutated() renames the buffer in place,
        # so a mutated tensor has the same id but a different name,
        # causing a cache miss.
        cache_key = None
        if config.cache_sdpa_constraint:
            arg_name = arg.maybe_get_name()
            cache_key = (
                id(arg),
                arg_name,
                tuple(stride_order) if stride_order else None,
            )
            if cache_key in V.graph.sdpa_constraint_cache:
                return V.graph.sdpa_constraint_cache[cache_key]

        result = _apply_constraint_inner(
            idx, arg, meta_val, meta_stride_expr, stride_order
        )
        if cache_key is not None:
            V.graph.sdpa_constraint_cache[cache_key] = result
        return result