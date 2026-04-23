def _fetch_proxies_and_all_constant_flag(
    flat_args_kwargs: list[object] | tuple[object, ...], tracer: _ProxyTracer
) -> tuple[list[object], tuple[object, ...], bool]:
    """
    Given flat arguments, fetch the proxies and whether they are all constants.
    This is later used in proxy_call or when someone is trying to stitch together
    graph node in tf or td modes.
    """
    f_flat_args_kwargs = [
        (
            fetch_object_proxy(tracer, x)
            if isinstance(x, (Tensor, _AnyScriptObject)) or is_opaque_value(x)
            else x
        )
        for x in flat_args_kwargs
    ]

    # If there are SymInts, we also should not consider this constant.
    # However, fake tensor handling of SymInts is sufficiently broken that
    # I couldn't write a test for this case
    all_constant = (
        not any(
            t.constant is None
            for t in f_flat_args_kwargs
            if isinstance(t, _ProxyTensor)
        )
        # TODO: maybe constant SymInts should also be allowed?  Not sure if
        # this can happen
        and not any(isinstance(x, py_sym_types) for x in flat_args_kwargs)
    )

    proxy_flat_args_kwargs = [
        e.proxy if isinstance(e, _ProxyTensor) else e for e in f_flat_args_kwargs
    ]

    proxy_flat_args_kwargs = [
        (fetch_sym_proxy(tracer)(e) if isinstance(e, py_sym_types) else e)
        for e in proxy_flat_args_kwargs
    ]

    return f_flat_args_kwargs, tuple(proxy_flat_args_kwargs), all_constant