def squeeze(x, dim=None):
    assert isinstance(x, TensorBox)
    if dim is None:
        return TensorBox(SqueezeView.create(x.data))

    dim = (
        V.graph.sizevars.guard_int(dim)
        if isinstance(dim, (int, sympy.Expr))
        else tuple(V.graph.sizevars.guard_int(d) for d in dim)
    )
    dim = canonicalize_dims(len(x.get_size()), dim)  # type: ignore[call-overload]
    dims = OrderedSet((dim,) if not isinstance(dim, tuple) else dim)

    new_shape = []
    for d, s in enumerate(x.get_size()):
        if not (d in dims and V.graph.sizevars.guard_or_false(sympy.Eq(s, 1))):
            new_shape.append(s)

    # squeeze does nothing if the size isn't 1
    return view(x, new_shape) if new_shape != x.get_size() else x