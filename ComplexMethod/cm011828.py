def pow(a, b):
    if isinstance(b, float) and b.is_integer():
        return pow(a, int(b))
    elif isinstance(b, float) and b == 0.5:
        return sqrt(a)
    elif isinstance(b, int) and b == 1:
        return clone(a)

    # Type promotion ensures all tensor arguments have the same type
    dtype = next(x.get_dtype() for x in (a, b) if isinstance(x, ir.TensorBox))
    is_integer_pow = is_integer_dtype(dtype)

    # Optimize away small fixed powers, or for integers avoid falling back to ATen
    embed_exponent = isinstance(b, int) and (
        -32 < b < 32 or (is_integer_pow and b >= 0)
    )
    if embed_exponent:
        loader = a.make_loader()

        def fn(idx):
            return pow_recursive(loader(idx), b, a.get_dtype())

        return Pointwise.create(
            device=a.get_device(),
            dtype=a.get_dtype(),
            inner_fn=fn,
            ranges=a.get_size(),
        )

    if isinstance(a, Number):
        if a == 1:
            return full_like(b, 1)

        if a == 2 and is_float_dtype(b.get_dtype()):
            return exp2(b)

    if is_integer_pow:
        # ops.pow doesn't work for integers
        if isinstance(a, Number):
            return fallback_pow_scalar(a, b)
        elif isinstance(b, Number):
            return fallback_pow_tensor_scalar(a, b)
        else:
            return fallback_pow_tensor_tensor(a, b)

    return pow_native(a, b)