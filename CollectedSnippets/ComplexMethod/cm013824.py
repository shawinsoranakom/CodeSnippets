def mean(
    input: Tensor | MaskedTensor,
    dim: DimOrDims = None,
    *,
    keepdim: bool | None = False,
    dtype: DType | None = None,
    mask: Tensor | None = None,
) -> Tensor:
    """\
{reduction_signature}

{reduction_descr}

By definition, the identity value of a mean operation is the mean
value of the tensor. If all elements of the input tensor along given
dimension(s) :attr:`dim` are masked-out, the identity value of the
mean is undefined.  Due to this ambiguity, the elements of output
tensor with strided layout, that correspond to fully masked-out
elements, have ``nan`` values.

{reduction_args}

{reduction_example}"""
    dtype_source = "Optional"
    if dtype is None:
        dtype = input.dtype
        dtype_source = "Input"

    if not (dtype.is_floating_point or dtype.is_complex):
        raise ValueError(
            f"mean(): Could not infer output dtype. {dtype_source} dtype must be either "
            f"a floating point or complex dtype. Got: {dtype}"
        )
    if input.layout == torch.strided:
        if mask is None:
            # TODO: compute count analytically
            # pyrefly: ignore [no-matching-overload]
            count = sum(
                torch.ones(input.shape, dtype=torch.int64, device=input.device),
                dim,
                keepdim=keepdim,
            )
            # pyrefly: ignore [no-matching-overload]
            total = sum(input, dim, keepdim=keepdim, dtype=dtype)
        else:
            inmask = _input_mask(input, mask=mask)
            count = inmask.sum(dim=dim, keepdim=bool(keepdim))
            # pyrefly: ignore [no-matching-overload]
            total = sum(input, dim, keepdim=keepdim, dtype=dtype, mask=inmask)
        return total / count
    elif input.layout == torch.sparse_csr:
        mask_input = _combine_input_and_mask(mean, input, mask)
        dim_ = _canonical_dim(dim, mask_input.ndim)
        if mask is None:
            raise ValueError(
                "masked mean expects explicit mask for sparse_csr tensor input"
            )
        return _sparse_csr_segment_reduction_helper(
            torch.mean, mask_input, dim_, bool(keepdim), dtype
        )
    else:
        raise ValueError(
            f"masked mean expects strided or sparse_csr tensor (got {input.layout} tensor)"
        )