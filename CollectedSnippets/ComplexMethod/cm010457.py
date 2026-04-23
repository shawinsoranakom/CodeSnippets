def jagged_from_list(
    tensors: List[torch.Tensor],
    offsets: Optional[torch.Tensor],
    dtype=None,
    device=None,
) -> tuple[NestedTensor, torch.Tensor]:
    """Constructs a NestedTensor backed by jagged layout from a list of tensors"""

    if len(tensors) == 0:
        raise RuntimeError("Cannot construct a nested tensor from an empty tensor list")
    if not len(set(t.dtype for t in tensors)) == 1:  # noqa: C401
        raise RuntimeError(
            "When constructing a nested tensor, all tensors in list must have the same dtype"
        )
    if not len(set(t.device for t in tensors)) == 1:  # noqa: C401
        raise RuntimeError(
            "When constructing a nested tensor, all tensors in list must be on the same device"
        )
    if not len(set(t.dim() for t in tensors)) == 1:  # noqa: C401
        raise RuntimeError(
            "When constructing a nested tensor, all tensors in list must have the same dim"
        )
    component_dim = tensors[0].dim()
    if component_dim == 0:
        raise RuntimeError(
            "Cannot construct a nested tensor from a list of zero-dim tensors"
        )

    # Check that the NT is representable by the jagged layout, which
    # allows for a single ragged dimension after the batch dim.
    # e.g. (B, *, D_0, ..., D_N), (B, D_0, *, ..., D_N), etc.
    sizes = [t.shape for t in tensors]
    ragged_idx = None
    for d in range(component_dim):
        dim_is_ragged = any(size[d] != sizes[0][d] for size in sizes)
        if dim_is_ragged:
            if ragged_idx is None:
                # add 1 to convert to outer NJT dim space
                ragged_idx = d + 1
            else:
                raise RuntimeError(
                    "Cannot represent given tensor list as a nested tensor with the jagged layout. "
                    "Note that the jagged layout only allows for a single ragged dimension. "
                    "For example: (B, *, D_0, D_1, ..., D_N), with ragged * dim."
                )

    # allow for a rectangular NJT and default the ragged dim next to the batch dim
    if ragged_idx is None:
        ragged_idx = 1

    # Set properties appropriately.
    values = torch.cat(tensors, dim=(ragged_idx - 1))
    to_kwargs = {}
    if device is not None:
        to_kwargs["device"] = device
    if dtype is not None:
        to_kwargs["dtype"] = dtype
    values = values.to(**to_kwargs)

    # Calculate jagged offsets if not provided.
    if offsets is None:
        # Jagged layout specifies that offsets are stored as int64 on the same device as values.
        # TODO: An alternative way to construct offsets is to use F.pad. This avoids creating
        # an extra leaf tensor during the forward, potentially resolving compatibility issues.
        offsets = torch.cat(
            [
                torch.zeros(1, dtype=torch.int64, device=values.device),
                torch.tensor(
                    [s[ragged_idx - 1] for s in sizes], device=values.device
                ).cumsum(dim=0),
            ]
        )

    # compute this now since it's easy
    min_seqlen = min(t.shape[ragged_idx - 1] for t in tensors)
    max_seqlen = max(t.shape[ragged_idx - 1] for t in tensors)
    ret_nt = nested_view_from_values_offsets(
        values,
        offsets,
        min_seqlen=min_seqlen,
        max_seqlen=max_seqlen,
        ragged_idx=ragged_idx,
    )
    return (ret_nt, offsets)