def auto_functionalized_dense(
    _mutable_op: OpOverload,
    _only_clone_these_tensors: tuple[str, ...] | None = None,
    **kwargs: Any,
) -> tuple[Any, tuple[Tensor, ...]]:
    new_kwargs = dict(**kwargs)
    result = []

    _mutable_args_names, _ = get_mutable_args(_mutable_op)
    for name in _mutable_args_names:
        if (
            _only_clone_these_tensors is not None
            and name not in _only_clone_these_tensors
        ):
            new_kwargs[name] = kwargs[name]
        else:
            new_kwargs[name] = (
                [clone_preserve_strides(x) for x in kwargs[name]]
                if kwargs[name] is not None and isinstance(kwargs[name], list)
                else (
                    clone_preserve_strides(kwargs[name])
                    if kwargs[name] is not None
                    else None
                )
            )
        result.append(new_kwargs[name])
    out = _mutable_op(**new_kwargs)

    if isinstance(out, tuple):
        return (*out, *result)  # type: ignore[return-value]
    else:
        return (out, *result)