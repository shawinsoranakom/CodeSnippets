def _mha_shape_check(
    query: Tensor,
    key: Tensor,
    value: Tensor,
    key_padding_mask: Tensor | None,
    attn_mask: Tensor | None,
    num_heads: int,
):
    # Verifies the expected shape for `query, `key`, `value`, `key_padding_mask` and `attn_mask`
    # and returns if the input is batched or not.
    # Raises an error if `query` is not 2-D (unbatched) or 3-D (batched) tensor.

    # Shape check.
    if query.dim() == 3:
        # Batched Inputs
        is_batched = True
        if key.dim() != 3 or value.dim() != 3:
            raise AssertionError(
                "For batched (3-D) `query`, expected `key` and `value` to be 3-D"
                f" but found {key.dim()}-D and {value.dim()}-D tensors respectively"
            )
        if key_padding_mask is not None:
            if key_padding_mask.dim() != 2:
                raise AssertionError(
                    "For batched (3-D) `query`, expected `key_padding_mask` to be `None` or 2-D"
                    f" but found {key_padding_mask.dim()}-D tensor instead"
                )
        if attn_mask is not None:
            if attn_mask.dim() not in (2, 3):
                raise AssertionError(
                    "For batched (3-D) `query`, expected `attn_mask` to be `None`, 2-D or 3-D"
                    f" but found {attn_mask.dim()}-D tensor instead"
                )
    elif query.dim() == 2:
        # Unbatched Inputs
        is_batched = False
        if key.dim() != 2 or value.dim() != 2:
            raise AssertionError(
                "For unbatched (2-D) `query`, expected `key` and `value` to be 2-D"
                f" but found {key.dim()}-D and {value.dim()}-D tensors respectively"
            )

        if key_padding_mask is not None:
            if key_padding_mask.dim() != 1:
                raise AssertionError(
                    "For unbatched (2-D) `query`, expected `key_padding_mask` to be `None` or 1-D"
                    f" but found {key_padding_mask.dim()}-D tensor instead"
                )

        if attn_mask is not None:
            if attn_mask.dim() not in (2, 3):
                raise AssertionError(
                    "For unbatched (2-D) `query`, expected `attn_mask` to be `None`, 2-D or 3-D"
                    f" but found {attn_mask.dim()}-D tensor instead"
                )
            if attn_mask.dim() == 3:
                expected_shape = (num_heads, query.shape[0], key.shape[0])
                if attn_mask.shape != expected_shape:
                    raise AssertionError(
                        f"Expected `attn_mask` shape to be {expected_shape} but got {attn_mask.shape}"
                    )
    else:
        raise AssertionError(
            f"query should be unbatched 2D or batched 3D tensor but received {query.dim()}-D query tensor"
        )

    return is_batched