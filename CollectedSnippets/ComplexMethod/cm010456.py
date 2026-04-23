def _nested_from_padded_tensor_default(func, *args, **kwargs):
    _, new_kwargs = normalize_function(  # type: ignore[misc]
        func, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
    )

    padded, offsets = new_kwargs["padded"], new_kwargs["offsets"]
    ragged_idx = new_kwargs.get("ragged_idx", 1)

    # only 3D padded with ragged packed dim=0 is supported by the underlying FBGEMM
    # kernel so do shape gymnastics
    if ragged_idx > 1:
        padded = padded.transpose(ragged_idx, 1)
    padded_ragged_dim1_shape = padded.shape
    if padded.dim() > 3:
        padded = padded.flatten(start_dim=2)
    elif padded.dim() < 3:
        padded = padded.unsqueeze(-1)

    # NB: The CUDA kernel for padded dense -> jagged conversion does not support
    # integer / bool types; work around this by casting to half.
    is_bool = padded.dtype is torch.bool
    if is_bool and padded.is_cuda:
        padded = padded.to(torch.half)
    values = torch.ops.aten._padded_dense_to_jagged_forward(
        padded, [offsets], new_kwargs["sum_S"]
    )
    if is_bool and values.is_cuda:
        values = values.to(torch.bool)

    # shape gymnastics part 2
    if len(padded_ragged_dim1_shape) > 3:
        values = values.unflatten(-1, padded_ragged_dim1_shape[2:])
    elif len(padded_ragged_dim1_shape) < 3:
        values = values.squeeze(-1)
    if ragged_idx > 1:
        values = values.transpose(ragged_idx - 1, 0)

    min_seqlen = new_kwargs["min_seqlen"]
    max_seqlen = new_kwargs["max_seqlen"]
    metadata_cache = {}
    if min_seqlen is not None:
        metadata_cache["min_seqlen"] = min_seqlen
    if max_seqlen is not None:
        metadata_cache["max_seqlen"] = max_seqlen

    return NestedTensor(
        values,
        offsets,
        _ragged_idx=ragged_idx,
        _metadata_cache=metadata_cache,
    )