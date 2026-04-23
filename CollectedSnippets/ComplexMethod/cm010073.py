def meta_sparse_structured_linear(
    input: Tensor,
    weight: Tensor,
    _meta: Tensor,
    bias: Tensor | None = None,
    _activation_opt: str | None = None,
    out_dtype: torch.dtype | None = None,
):
    output_sizes = list(input.shape)
    if bias is not None:
        if weight.size(0) != bias.size(0):
            raise AssertionError(
                f"output size mismatch: weight.size(0)={weight.size(0)} != bias.size(0)={bias.size(0)}"
            )
    if weight.size(1) != input.size(-1) / 2:
        raise AssertionError(
            f"weight.size(1)={weight.size(1)} != input.size(-1)/2={input.size(-1) / 2}"
        )
    output_sizes[-1] = weight.size(0)

    # see: https://github.com/pytorch/pytorch/pull/114477#issuecomment-1830121375
    # We assume that we have already squashed the inputs into a 2-D tensor
    # Then, as the output is transposed, we need to propagate the transposed
    # stride information to the output tensor
    if len(input.shape) != 2:
        raise AssertionError(
            f"we can only handle the squashed input case, got {len(input.shape)}D input"
        )
    transposed_strides = (1, input.size(0))

    if out_dtype is not None:
        if not (input.dtype == torch.int8 and out_dtype == torch.int32):
            raise AssertionError(
                f"out_dtype is only supported for i8i8->i32 linear operator, got input.dtype={input.dtype}, out_dtype={out_dtype}"
            )
    output = input.new_empty_strided(
        output_sizes,
        transposed_strides,
        dtype=input.dtype if out_dtype is None else out_dtype,
    )

    return output