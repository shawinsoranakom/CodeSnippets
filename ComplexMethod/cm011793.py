def promote_constants(inputs, override_return_dtype=None, type_promotion_kind=None):
    assert override_return_dtype is None or type_promotion_kind is None, (
        "only one of override_return_dtype or type_promotion_kind may be given"
    )

    if override_return_dtype is None and type_promotion_kind is None:
        type_promotion_kind = ELEMENTWISE_TYPE_PROMOTION_KIND.DEFAULT

    if not any(isinstance(x, (sympy.Basic, int, float)) for x in inputs):
        return inputs
    if all(isinstance(x, (int, float, sympy.Basic)) for x in inputs):
        dtype = override_return_dtype or get_promoted_dtype(
            *inputs,
            # pyrefly: ignore [bad-argument-type]
            type_promotion_kind=type_promotion_kind,
        )

        def const_func(x):
            if isinstance(x, sympy.Basic):
                return ir.IndexingConstant(
                    index=x, dtype=dtype, device=decode_device(None)
                )
            else:
                return ir.Constant(value=x, dtype=dtype, device=decode_device(None))

        return [const_func(x) for x in inputs]
    ex = next(x for x in inputs if isinstance(x, (TensorBox, ExpandView, ir.Constant)))
    tensor_dtype = ex.get_dtype()

    # Round scalar to tensor's dtype for comparison ops to match eager
    if override_return_dtype == torch.bool and tensor_dtype in (
        torch.bfloat16,
        torch.float16,
    ):
        _round_scalar = lambda v: torch.tensor(v, dtype=tensor_dtype).item()  # noqa: E731
    else:
        _round_scalar = lambda v: v  # noqa: E731

    out = []
    for x in inputs:
        if isinstance(x, (int, float)):
            out.append(
                ExpandView.create(
                    ir.Constant(
                        value=_round_scalar(x),
                        dtype=tensor_dtype,
                        device=ex.get_device_or_error(),
                    ),
                    list(ex.get_size()),
                )
            )
        elif isinstance(x, sympy.Basic):
            out.append(
                ExpandView.create(
                    IndexingConstant(
                        index=x, dtype=tensor_dtype, device=ex.get_device_or_error()
                    ),
                    list(ex.get_size()),
                )
            )
        else:
            out.append(x)

    return out