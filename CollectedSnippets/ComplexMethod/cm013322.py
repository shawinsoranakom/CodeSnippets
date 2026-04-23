def generate_elementwise_binary_large_value_tensors(
    op, *, device, dtype, requires_grad=False
):
    _large_int_vals = (-1113, 1113, -10701, 10701)
    _large_float16_vals = (-501, 501, -1001.2, 1001.2, -13437.7, 13437.7)
    _large_float_vals = _large_float16_vals + (-4988429.2, 4988429.2, -1e20, 1e20)
    _large_uint_vals = (1113, 10701, 60000)

    l_vals = []
    r_vals = []

    if dtype == torch.float16:
        prod = product(_large_float16_vals, _large_float16_vals)
    elif dtype.is_floating_point:
        prod = product(_large_float_vals, _large_float_vals)
    elif dtype.is_complex:
        complex_vals = product(_large_float_vals, _large_float_vals)
        # Note the use of list is required here or the map generator will be
        #  emptied by the following product and it won't produce the desired cross-product
        complex_vals = [complex(*x) for x in complex_vals]
        prod = product(complex_vals, complex_vals)
    elif dtype in (torch.int16, torch.int32, torch.int64):
        prod = product(_large_int_vals, _large_int_vals)
    elif dtype in (torch.uint16, torch.uint32, torch.uint64):
        prod = product(_large_uint_vals, _large_uint_vals)
    else:
        raise ValueError("Unsupported dtype!")

    for l, r in prod:
        l_vals.append(l)
        r_vals.append(r)

    lhs = torch.tensor(l_vals, device=device, dtype=dtype, requires_grad=requires_grad)
    rhs = torch.tensor(r_vals, device=device, dtype=dtype, requires_grad=requires_grad)

    yield SampleInput(lhs, args=(rhs,), kwargs=op.sample_kwargs(device, dtype, lhs)[0])