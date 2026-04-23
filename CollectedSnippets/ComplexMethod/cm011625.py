def _check_strides_helper(
    a: TensorLikeType,
    b: TensorLikeType,
    *,
    only_cuda=True,
    significant_only=True,
    allow_rhs_unbacked=False,
) -> tuple[bool, int | None]:
    # NOTE: only on CUDA because CPU elementwise strides are incorrect in PyTorch
    # See https://github.com/pytorch/pytorch/issues/77553
    # Only compares strides that are "meaningful" -- strides for dimensions with length > 1
    # and for tensors with more than one element
    if (
        not only_cuda or a.device.type == "cuda" or b.device.type == "cuda"
    ) and a.numel() > 0:
        for idx in range(a.ndim):
            check = not significant_only or a.shape[idx] > 1
            # TODO: Check the symbols are consistent with each other
            if isinstance(b.stride()[idx], torch.SymInt):
                continue
            if a.stride()[idx] != b.stride()[idx] and check:
                return False, idx

    return True, None