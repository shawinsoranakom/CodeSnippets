def _use_flex_decoding(query, kv_indices, value, kernel_options, enable_gqa) -> bool:
    """Decide which kernel to use, return true if use flex decoding kernel.
    Note:
       Since the number of splits is calculated based of the number of batch and head dims
       we need to ensure that the batch and head dims are statically known. Otherwise we just
       use the main flex_attention kernel.
    """
    force_flex = kernel_options.get("FORCE_USE_FLEX_ATTENTION", False)

    short_query_length = V.graph.sizevars.evaluate_expr(
        sympy.Lt(query.get_size()[-2], 128)
    )
    non_zero_length = V.graph.sizevars.evaluate_expr(sympy.Gt(query.get_size()[-2], 0))
    static_batch = isinstance(query.get_size()[0], (int, sympy.Integer))
    static_num_heads = isinstance(query.get_size()[1], (int, sympy.Integer))
    if enable_gqa:
        # in the current flex decoding triton kernel, grouped query heads for the
        # same kv head are handled by the same block. So it's hard to support different
        # kv num blocks for grouped query heads. We just fall back to main flex_attention
        # kernel where each query head is handled by a separate block.
        valid_block_mask_num_heads = V.graph.sizevars.evaluate_expr(
            sympy.Eq(kv_indices.get_size()[1], 1)
        )
    else:
        valid_block_mask_num_heads = V.graph.sizevars.evaluate_expr(
            sympy.Or(
                sympy.Eq(kv_indices.get_size()[1], 1),
                sympy.Eq(kv_indices.get_size()[1], query.get_size()[1]),
            )
        )

    Hq = query.get_size()[1]
    Hkv = value.get_size()[1]
    ratio = FloorDiv(Hq, Hkv)

    pw_of_two = V.graph.sizevars.guard_or_false(
        sympy.And(sympy.Gt(ratio, 0), sympy.Eq(ratio & (ratio - 1), 0))
    )

    out = (
        not force_flex
        and not kernel_options.get("OUTPUT_MAX", False)
        and short_query_length
        and static_batch
        and static_num_heads
        and non_zero_length
        and valid_block_mask_num_heads
        and pw_of_two
    )
    log.debug(
        "Use flex decoding %s, force_flex_attention=%s, short_query_length=%s, static_batch=%s, static_num_heads=%s",
        out,
        force_flex,
        short_query_length,
        static_batch,
        static_num_heads,
    )
    return out