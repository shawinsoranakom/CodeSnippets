def foreach_run_and_map_input_device(
    fake_mode: FakeTensorMode, func: OpOverload, *args: Any, **kwargs: Any
) -> list[FakeTensor] | None:
    tensor_lists = [
        arg
        for arg in itertools.chain(args, kwargs.values())
        if isinstance(arg, (list, tuple))
        and len(arg)
        and isinstance(arg[0], torch.Tensor)
    ]

    try:
        with in_kernel_invocation_manager(fake_mode):
            out_meta = func(*args, **kwargs)
    except NotImplementedError:
        return NotImplemented

    if not out_meta:
        return out_meta

    if not tensor_lists:
        raise AssertionError("tensor_lists must not be empty")
    out_fake = []

    for i, meta_t in enumerate(out_meta):
        device, _ = FakeTensor._find_common_device(func, [tl[i] for tl in tensor_lists])
        out_fake.append(
            fake_mode.fake_tensor_converter.from_meta_and_device(
                fake_mode, meta_t, device
            )
        )

    return out_fake