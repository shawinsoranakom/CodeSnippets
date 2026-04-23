def where(cond, a, b):
    def fn(*args):
        return ops.where(*args)

    if isinstance(a, (float, int)):
        a = constant_like(a)(b)
    if isinstance(b, (float, int)):
        b = constant_like(b)(a)

    args = [cond, a, b]
    dtype = get_promoted_dtype(
        args[1], args[2], type_promotion_kind=ELEMENTWISE_TYPE_PROMOTION_KIND.DEFAULT
    )
    indices = [i for i, x in enumerate(args) if isinstance(x, TensorBox)]
    for i, x in zip(indices, broadcast_tensors(*[args[i] for i in indices])):
        args[i] = x
    for i in range(len(args)):
        if isinstance(args[i], ir.Constant):
            args[i] = ExpandView.create(args[i], list(args[indices[0]].get_size()))
    return make_pointwise(fn, override_return_dtype=dtype)(
        args[0], to_dtype(args[1], dtype), to_dtype(args[2], dtype)
    )