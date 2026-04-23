def _to_will_alias(
    a: TensorLikeType,
    device: DeviceLikeType | None = None,
    dtype: torch.dtype | None = None,
    copy: bool | None = None,
    layout: torch.layout | None = None,
    memory_format: torch.memory_format | None = None,
    pin_memory: bool | None = False,
    non_blocking: bool = False,  # not using non_blocking
) -> bool:
    return (
        not copy
        and (device is None or a.device == device)
        and (dtype is None or a.dtype == dtype)
        and (layout is None or a.layout == layout)
        # is_pinned issue #84925
        # and (pin_memory is None or pin_memory == a.is_pinned())
        and (
            memory_format is None
            or memory_format == torch.preserve_format
            or utils.is_contiguous_for_memory_format(a, memory_format=memory_format)
        )
    )