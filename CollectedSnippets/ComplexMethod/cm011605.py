def meshgrid(
    *tensors: TensorLikeType | list[TensorLikeType] | tuple[TensorLikeType],
    indexing: str,
) -> list[TensorLikeType]:
    # This ref simultaneously handles two overloads (see stubs above)
    # The `indexing` argument is currently optional for torch.meshgrid, but we
    # plan to make the argument required: https://github.com/pytorch/pytorch/issues/50276
    if isinstance(tensors[0], (list, tuple)):
        if len(tensors) != 1:
            raise AssertionError(
                f"Expected exactly 1 tensor list/tuple, got {len(tensors)}"
            )
        tensors = tuple(tensors[0])

    torch._check(
        builtins.all(isinstance(a, TensorLike) for a in tensors),
        lambda: "meshgrid expects its inputs to be tensors",
    )

    torch._check(len(tensors) > 0, lambda: "meshgrid expects a non-empty TensorList")

    for i in range(len(tensors) - 1):
        torch._check(
            tensors[i].dtype == tensors[i + 1].dtype,  # type: ignore[union-attr]
            lambda: "meshgrid expects all tensors to have the same dtype",
        )
        torch._check(
            tensors[i].device == tensors[i + 1].device,  # type: ignore[union-attr]
            lambda: "meshgrid expects all tensors to have the same device",
        )

    swap_first_and_second_tensors = False
    if indexing == "xy":
        swap_first_and_second_tensors = len(tensors) >= 2
        if swap_first_and_second_tensors:
            tensors = (tensors[1], tensors[0], *tensors[2:])
    else:
        torch._check(
            indexing == "ij",
            lambda: (
                'torch.meshgrid: indexing must be one of "xy" or "ij", '
                f"but received: {indexing}"
            ),
        )

    result_shape: list[int] = []
    for t in tensors:
        if not isinstance(t, TensorLike):
            raise AssertionError(f"expected TensorLike, got {type(t)}")  # mypy
        torch._check(
            t.ndim == 0 or t.ndim == 1,
            lambda: f"torch.meshgrid: Expected 0D or 1D tensor in the tensor list but got: {t}",
        )
        result_shape.append(t.numel())

    grids: list[TensorLikeType] = []
    for i, t in enumerate(tensors):
        if not isinstance(t, TensorLike):
            raise AssertionError(f"expected TensorLike, got {type(t)}")  # mypy
        if t.ndim == 0:
            t = t.view((1,))
        grids.append(prims.broadcast_in_dim(t, result_shape, (i,)))

    if swap_first_and_second_tensors:
        # Swap outputs if we originally swapped at the beginning
        grids[0], grids[1] = grids[1], grids[0]

    return grids