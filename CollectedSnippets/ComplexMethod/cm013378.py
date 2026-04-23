def einsum(*operands, out=None, dtype=None, order="K", casting="safe", optimize=False):
    # Have to manually normalize *operands and **kwargs, following the NumPy signature
    # We have a local import to avoid polluting the global space, as it will be then
    # exported in funcs.py
    from ._ndarray import ndarray
    from ._normalizations import (
        maybe_copy_to,
        normalize_array_like,
        normalize_casting,
        normalize_dtype,
        wrap_tensors,
    )

    dtype = normalize_dtype(dtype)
    casting = normalize_casting(casting)
    if out is not None and not isinstance(out, ndarray):
        raise TypeError("'out' must be an array")
    if order != "K":
        raise NotImplementedError("'order' parameter is not supported.")

    # parse arrays and normalize them
    sublist_format = not isinstance(operands[0], str)
    if sublist_format:
        # op, str, op, str ... [sublistout] format: normalize every other argument

        # - if sublistout is not given, the length of operands is even, and we pick
        #   odd-numbered elements, which are arrays.
        # - if sublistout is given, the length of operands is odd, we peel off
        #   the last one, and pick odd-numbered elements, which are arrays.
        #   Without [:-1], we would have picked sublistout, too.
        array_operands = operands[:-1][::2]
    else:
        # ("ij->", arrays) format
        subscripts, array_operands = operands[0], operands[1:]

    tensors = [normalize_array_like(op) for op in array_operands]
    target_dtype = _dtypes_impl.result_type_impl(*tensors) if dtype is None else dtype

    # work around 'bmm' not implemented for 'Half' etc
    is_half = target_dtype == torch.float16 and all(t.is_cpu for t in tensors)
    if is_half:
        target_dtype = torch.float32

    is_short_int = target_dtype in [torch.uint8, torch.int8, torch.int16, torch.int32]
    if is_short_int:
        target_dtype = torch.int64

    tensors = _util.typecast_tensors(tensors, target_dtype, casting)

    from torch.backends import opt_einsum

    try:
        # set the global state to handle the optimize=... argument, restore on exit
        if opt_einsum.is_available():
            old_strategy = torch.backends.opt_einsum.strategy
            old_enabled = torch.backends.opt_einsum.enabled

            # torch.einsum calls opt_einsum.contract_path, which runs into
            # https://github.com/dgasmith/opt_einsum/issues/219
            # for strategy={True, False}
            if optimize is True:
                optimize = "auto"
            elif optimize is False:
                torch.backends.opt_einsum.enabled = False

            torch.backends.opt_einsum.strategy = optimize

        if sublist_format:
            # recombine operands
            sublists = operands[1::2]
            has_sublistout = len(operands) % 2 == 1
            if has_sublistout:
                sublistout = operands[-1]
            operands = list(itertools.chain.from_iterable(zip(tensors, sublists)))
            if has_sublistout:
                operands.append(sublistout)

            result = torch.einsum(*operands)
        else:
            result = torch.einsum(subscripts, *tensors)

    finally:
        if opt_einsum.is_available():
            torch.backends.opt_einsum.strategy = old_strategy
            torch.backends.opt_einsum.enabled = old_enabled

    result = maybe_copy_to(out, result)
    return wrap_tensors(result)