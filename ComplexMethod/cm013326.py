def _reference_inputs_elementwise_unary(op, device, dtype, requires_grad, **kwargs):
    yield from op.sample_inputs_func(op, device, dtype, requires_grad, **kwargs)

    yield from generate_elementwise_unary_tensors(
        op, device=device, dtype=dtype, requires_grad=requires_grad, **kwargs
    )

    if dtype is not torch.bool:
        yield from generate_elementwise_unary_small_value_tensors(
            op, device=device, dtype=dtype, requires_grad=requires_grad, **kwargs
        )
    if dtype not in (torch.bool, torch.uint8, torch.int8) and (
        op.handles_large_floats
        or (not dtype.is_floating_point and not dtype.is_complex)
    ):
        yield from generate_elementwise_unary_large_value_tensors(
            op, device=device, dtype=dtype, requires_grad=requires_grad, **kwargs
        )

    if dtype.is_floating_point or (
        op.handles_complex_extremal_values and dtype.is_complex
    ):
        yield from generate_elementwise_unary_extremal_value_tensors(
            op, device=device, dtype=dtype, requires_grad=requires_grad, **kwargs
        )