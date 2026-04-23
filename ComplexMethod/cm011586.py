def to(a: TensorLikeType, *args, **kwargs) -> TensorLikeType:
    # handled dispatch via positional arguments
    if len(args) != 0:
        kwargs = _to_dispatch(*args, **kwargs)

    # TODO: is_pinned is not currently supported in refs or fake_tensor
    # https://github.com/pytorch/pytorch/issues/84925
    if "pin_memory" in kwargs:
        raise AssertionError("pin_memory is not supported in refs")
    _canonicalize_to_arguments(a, kwargs)

    if _to_will_alias(a, **kwargs):
        return a

    copy = kwargs.pop("copy") if "copy" in kwargs else False
    non_blocking = kwargs.pop("non_blocking") if "non_blocking" in kwargs else False

    # short-circuit to `prims.convert_element_type` when `to` is just a dtype change
    if (
        (copy or (kwargs.get("dtype", a.dtype) != a.dtype))
        and (not non_blocking)
        and ("memory_format" not in kwargs)
        and ("device" not in kwargs)
        and ("layout" not in kwargs)
        # is_pinned issue #84925
        # and ("pin_memory" not in kwargs)
    ):
        return prims.convert_element_type(a, kwargs.get("dtype", a.dtype))

    result = torch.empty_like(a, **kwargs)
    # TODO: non_blocking should be handled by `copy_to`
    copy_to(result, a)
    return result