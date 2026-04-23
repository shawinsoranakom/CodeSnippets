def group_foreach_args(
    arg_pairs: Iterable[Any],
) -> defaultdict[tuple[Any, bool], list[tuple[int, Any]]]:
    out = defaultdict(list)
    unpack_args = False
    for i, args in enumerate(arg_pairs):
        if not isinstance(args, Iterable):
            unpack_args = True
            args = (args,)
        use_foreach = (
            not is_dynamic(*args) or config.combo_kernel_foreach_dynamic_shapes
        )
        device = None
        for t in args:
            if isinstance(t, TensorBox):
                device = t.data.get_device()
                break
        assert device is not None, "foreach op should have at least one tensor arg"
        if unpack_args:
            (args,) = args
        out[(device, use_foreach)].append((i, args))
    return out