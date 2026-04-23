def _fused_rms_norm(
    input: Tensor,
    normalized_shape: list[int],
    weight: Tensor | None,
    eps: float | None,
) -> tuple[Tensor, Tensor]:
    dims_to_reduce: list[int] = []
    for i in range(len(normalized_shape)):
        dims_to_reduce.append(input.dim() - i - 1)

    # upcast is needed for fp16 and bf16
    computation_dtype = utils.get_computation_dtype(input.dtype)
    upcasted_input = input.to(computation_dtype)

    # computation_dtype would be one of [Double, Float, ComplexFloat, ComplexDouble]
    if eps is None:
        if computation_dtype in (torch.float32, torch.complex64):
            eps_val = torch.finfo(torch.float32).eps
        else:
            eps_val = torch.finfo(torch.float64).eps
    else:
        eps_val = eps

    rqrst_input = torch.rsqrt(
        # NB: don't inplace here, will violate functional IR invariant
        # NB: carefully use the Scalar overload of add to ensure compatibility with the C++ decomp
        torch.ops.aten.add.Scalar(
            torch.pow(upcasted_input, 2).mean(dim=dims_to_reduce, keepdim=True), eps_val
        )
    )

    upcasted_result = upcasted_input.mul(rqrst_input)

    if weight is not None:
        upcasted_result = upcasted_result.mul(weight)

    # NB: nested should be dead here, just here for fidelity
    is_nested = input.is_nested or (weight is not None and weight.is_nested)
    memory_format = utils.suggest_memory_format(input)
    is_channels_last = memory_format in (
        torch.channels_last,
        torch.channels_last_3d,
    )

    if not is_nested and not is_channels_last:
        upcasted_result = upcasted_result.contiguous()
        rqrst_input = rqrst_input.contiguous()

    # Cast normalized result back to original input type
    result = upcasted_result.type_as(input)

    return result, rqrst_input