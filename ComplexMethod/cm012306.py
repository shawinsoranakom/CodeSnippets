def can_pad(
    mat1: Tensor,
    mat2: Tensor,
    op: torch._ops.OpOverloadPacket,
    input: Tensor | None = None,
) -> bool:
    """
    Determines if an operation CAN be padded (safety checks).
    All logic related to whether it's safe to pad should be here.
    """

    # Can't pad if there is no static dims, we pad static dims only.
    def has_one_static_dim(t: Tensor) -> bool:
        """Return False if all dimensions are symbolic — nothing concrete to pad."""
        for x in t.size():
            if isinstance(x, int):
                return True
            elif not isinstance(x, torch.SymInt):
                raise RuntimeError("not expected size")
        return False

    # Basic safety checks
    if not torch._inductor.config.shape_padding:
        return False

    if not check_device(mat1, mat2):
        return False

    if not check_dtype(mat1, mat2):
        return False

    # For padding to be vaible each tensor should have at least one static dim.
    tensors = [t for t in (mat1, mat2, input) if t is not None]
    if not all(has_one_static_dim(t) for t in tensors):
        return False

    # Skip zero-sized dimensions — padding would be wasteful (mm on empty tensors)
    from torch.fx.experimental.symbolic_shapes import optimization_hint

    if any(
        optimization_hint(dim) == 0 for dim in itertools.chain(mat1.shape, mat2.shape)
    ):
        return False

    # Calculate padding lengths to check if padding is needed
    with no_dispatch():
        if op is torch.ops.aten.mm or op is torch.ops.aten.addmm:
            m = mat1.shape[0]
            k = mat1.shape[1]
            n = mat2.shape[1]
        elif op is torch.ops.aten.bmm:
            m = mat1.shape[1]
            k = mat1.shape[2]
            n = mat2.shape[2]
        else:
            return False

        k_padded_length = get_padded_length(k, get_alignment_size(mat1))
        n_padded_length = get_padded_length(n, get_alignment_size(mat2))
        m_padded_length = get_padded_length(m, get_alignment_size(mat1))

        # No padding needed - can't pad if there's nothing to pad
        if m_padded_length == k_padded_length == n_padded_length == 0:
            return False

    # In deterministic mode, we can't safely benchmark - disallow padding
    # Check this after other basic checks so force_shape_pad/autoheuristic can override
    if (
        torch._inductor.config.deterministic
        and not torch._inductor.config.force_shape_pad
        and not torch._inductor.config.use_autoheuristic("pad_mm")
    ):
        return False

    # Triton availability check - required for padding to work
    if not has_triton():
        return False

    return True