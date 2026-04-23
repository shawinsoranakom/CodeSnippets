def _extract_tensor_metadata(
    result: torch.Tensor, include_contiguity=True
) -> TensorMetadata:
    """
    Extract a TensorMetadata NamedTuple describing `result`.
    """
    shape = result.shape
    dtype = result.dtype
    requires_grad = result.requires_grad
    stride = result.stride() if not is_sparse_any(result) else ()

    memory_format = None

    if include_contiguity and not is_sparse_any(result):
        memory_formats = (
            torch.contiguous_format,
            torch.channels_last,
            torch.channels_last_3d,
        )
        for query_format in memory_formats:
            if is_contiguous_for_memory_format_or_false(
                result, memory_format=query_format
            ):
                memory_format = query_format
                break

    is_quantized = result.is_quantized
    qparams: dict[str, Any] = {}
    if is_quantized:
        qscheme = result.qscheme()
        qparams["qscheme"] = qscheme
        if qscheme in (torch.per_tensor_affine, torch.per_tensor_symmetric):
            qparams["scale"] = result.q_scale()  # type: ignore[assignment]
            qparams["zero_point"] = result.q_zero_point()  # type: ignore[assignment]
        elif qscheme in (
            torch.per_channel_affine,
            torch.per_channel_affine_float_qparams,
            torch.per_channel_symmetric,
        ):
            # In this branch, scale and zero_point are expected to be tensors,
            # we store the values as immutable_list in TensorMetadata for
            # easier serialization downstream
            qparams["scale"] = result.q_per_channel_scales().tolist()  # type: ignore[assignment]
            qparams["zero_point"] = result.q_per_channel_zero_points().tolist()  # type: ignore[assignment]
            qparams["axis"] = result.q_per_channel_axis()  # type: ignore[assignment]

    return TensorMetadata(
        shape, dtype, requires_grad, stride, memory_format, is_quantized, qparams
    )