def validate_and_normalize_to_tuple(
    args: torch.Tensor
    | tuple[torch.Tensor, ...]
    | tuple[torch.Tensor | None, ...]
    | list[torch.Tensor]
    | list[torch.Tensor | None]
    | None,
    allow_none: bool = False,
) -> tuple[torch.Tensor | None, ...] | tuple[torch.Tensor, ...] | None:
    """Normalize ``args`` to a tuple and validate that all elements are tensors.

    Args:
        args: A single tensor, tuple/list of tensors, or ``None``.
        allow_none: If ``True``, permit ``None`` elements (for gradients).

    Returns:
        Tuple of tensors, or ``None`` if ``args`` is ``None``.

    Raises:
        PipeliningMetadataError: On non-tensor values
            (or ``None`` when ``allow_none=False``).
    """
    if args is None:
        return None
    elif isinstance(args, torch.Tensor):
        return (args,)
    elif isinstance(args, (tuple, list)):
        for i, arg in enumerate(args):
            if arg is None:
                if not allow_none:
                    raise PipeliningMetadataError(
                        f"Stage arg[{i}] is None. "
                        f"Stage args must be tensors. Use kwargs for optional values."
                    )
                continue
            if not isinstance(arg, torch.Tensor):
                raise PipeliningMetadataError(
                    f"Stage arg[{i}] has type {type(arg).__name__}. "
                    f"All stage args must be tensors. Use kwargs for non-tensor inputs."
                )
        # Normalize list to tuple
        return tuple(args) if isinstance(args, list) else args
    else:
        raise PipeliningMetadataError(
            f"Stage args must be a tensor, tuple, or list of tensors, got {type(args).__name__}."
        )