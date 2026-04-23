def get_supported_dtypes(op, sample_inputs_fn, device_type):
    # Returns the supported dtypes for the given operator and device_type pair.
    if device_type not in ["cpu", "cuda"]:
        raise AssertionError(
            f"Expected device_type in ['cpu', 'cuda'], got {device_type!r}"
        )
    if not TEST_CUDA and device_type == "cuda":
        warnings.warn(
            "WARNING: CUDA is not available, empty_dtypes dispatch will be returned!",
            stacklevel=2,
        )
        return _dynamic_dispatch_dtypes(())

    supported_dtypes = set()
    for dtype in all_types_and_complex_and(torch.bool, torch.bfloat16, torch.half):
        try:
            samples = sample_inputs_fn(op, device_type, dtype, False)
        except RuntimeError:
            # If `sample_inputs_fn` doesn't support sampling for a given
            # `dtype`, we assume that the `dtype` is not supported.
            # We raise a warning, so that user knows that this was the case
            # and can investigate if there was an issue with the `sample_inputs_fn`.
            warnings.warn(
                f"WARNING: Unable to generate sample for device:{device_type} and dtype:{dtype}",
                stacklevel=2,
            )
            continue

        # We assume the dtype is supported
        # only if all samples pass for the given dtype.
        supported = True
        for sample in samples:
            try:
                op(sample.input, *sample.args, **sample.kwargs)
            except RuntimeError:
                # dtype is not supported
                supported = False
                break

        if supported:
            supported_dtypes.add(dtype)

    return _dynamic_dispatch_dtypes(supported_dtypes)