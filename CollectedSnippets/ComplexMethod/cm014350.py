def _unpack_efficient_attention_nested_shapes(
    *,
    query,
    key,
    value,
    grad_out=None,
    cu_seqlens_q,
    cu_seqlens_k,
    max_seqlen_q,
    max_seqlen_k,
) -> Iterator[tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...], tuple[int, ...] | None]]:
    """
    Given inputs to a efficient_attention_(forward|backward) kernel, this will handle behavior for
    NestedTensor inputs by effectively unbinding the NestedTensor and yielding the shapes for
    each batch element.

    In the case that this isn't a NestedTensor kernel, then it just yields the original shapes.
    """
    if cu_seqlens_q is not None:
        # Unlike flash_attention_forward, we get a 4D tensor instead of a 3D tensor for efficient attention.
        #
        # This means we should be dealing with a Nested Jagged Tensor query.
        # The inputs will have shape                  (sum(sequence len), heads, dimension)
        # In comparison, non-Nested inputs have shape (batch, heads, sequence len, dimension)
        # To deal with this, we convert to a shape of (batch, heads, max_seq_len, dimension)
        # So the flops calculation in this case is an overestimate of the actual flops.
        if len(key.shape) != 4:
            raise AssertionError("_unpack_efficient_attention_nested_shapes: expected key.shape to be 4-dimensional")
        if len(value.shape) != 4:
            raise AssertionError("_unpack_efficient_attention_nested_shapes: expected value.shape to be 4-dimensional")
        if grad_out is not None and grad_out.shape != query.shape:
            raise AssertionError("_unpack_efficient_attention_nested_shapes: grad_out.shape must match query.shape when provided")
        _, _, h_q, d_q = query.shape
        _, _, h_k, d_k = key.shape
        _, _, h_v, d_v = value.shape
        if cu_seqlens_q is None:
            raise AssertionError("_unpack_efficient_attention_nested_shapes: cu_seqlens_q must not be None")
        if cu_seqlens_k is None:
            raise AssertionError("_unpack_efficient_attention_nested_shapes: cu_seqlens_k must not be None")
        if cu_seqlens_q.shape != cu_seqlens_k.shape:
            raise AssertionError("_unpack_efficient_attention_nested_shapes: "
                                 "cu_seqlens_q and cu_seqlens_k must have the same shape")
        seqlens_q = _offsets_to_lengths(cu_seqlens_q, max_seqlen_q)
        seqlens_k = _offsets_to_lengths(cu_seqlens_k, max_seqlen_k)
        for len_q, len_k in zip(seqlens_q, seqlens_k, strict=True):
            new_query_shape = (1, h_q, len_q, d_q)
            new_key_shape = (1, h_k, len_k, d_k)
            new_value_shape = (1, h_v, len_k, d_v)
            new_grad_out_shape = new_query_shape if grad_out is not None else None
            yield new_query_shape, new_key_shape, new_value_shape, new_grad_out_shape
        return

    yield query.shape, key.shape, value.shape, grad_out.shape if grad_out is not None else None