def _split_tensor(
    tensor: torch.Tensor,
    spec: TensorChunkSpec,
    num_chunks: int,
) -> Sequence[torch.Tensor]:
    """Given a tensor, and a chunking spec, split the tensor.
    Args:

        tensor: Tensor to split
        spec: Chunking spec
        num_chunks: Number of chunks to split the tensor into

    Returns:
        chunk_tensors: List of chunked tensors
    """

    if not tensor.size(spec.split_dim) >= num_chunks:
        raise AssertionError(
            f"Tensor size {tensor.size(spec.split_dim)} is smaller than num_chunks"
        )

    _is_dtensor = isinstance(tensor, DTensor)

    if _is_dtensor:
        # Use local_map to split locally and preserve placements.
        # Going through DTensor dispatch would convert Shard(split_dim) to
        # Replicate() via an implicit all-gather, which is both wasteful and
        # semantically wrong for PP microbatch splitting.
        placements = tensor.placements
        split_fn = local_map(
            lambda t: torch.tensor_split(t, num_chunks, spec.split_dim),
            out_placements=(placements,) * num_chunks,
            in_placements=(placements,),
        )
        chunk_tensors: Sequence[torch.Tensor] = split_fn(tensor)  # type: ignore[assignment]
    else:
        chunk_tensors = torch.tensor_split(tensor, num_chunks, spec.split_dim)

    # tensor_split on a leaf tensor produces non-leaf views that won't
    # accumulate .grad during torch.autograd.backward().  Call retain_grad()
    # on those views so that stage_backward() can read .grad from them.
    if tensor.requires_grad and tensor.is_leaf:
        for chunk in chunk_tensors:
            chunk.retain_grad()

    if not _debug_mask_minibatches:
        return chunk_tensors

    def _expand_chunks(
        orig: torch.Tensor, *chunks: torch.Tensor
    ) -> tuple[torch.Tensor, ...]:
        expanded = []
        idx = 0
        for chunk in chunks:
            new_val = torch.zeros_like(orig)
            upper = idx + chunk.size(spec.split_dim)
            slices: list[slice] = [slice(None)] * new_val.ndim
            slices[spec.split_dim] = slice(idx, upper)
            new_val[slices] = chunk
            expanded.append(new_val)
            idx += chunk.size(spec.split_dim)
        return tuple(expanded)

    if _is_dtensor:
        placements = tensor.placements
        n = len(chunk_tensors)
        expand_fn = local_map(
            _expand_chunks,
            out_placements=(placements,) * n,
            in_placements=(placements,) + (placements,) * n,
        )
        return list(expand_fn(tensor, *chunk_tensors))  # type: ignore[arg-type]
    else:
        return list(_expand_chunks(tensor, *chunk_tensors))