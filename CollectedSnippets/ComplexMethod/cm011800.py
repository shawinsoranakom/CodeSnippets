def repeat(x, repeats):
    old_size = list(x.get_size())
    if len(repeats) > len(old_size):
        old_size = [sympy.S.One] * (len(repeats) - len(old_size)) + old_size
        x = view(x, list(old_size))
    assert len(repeats) == len(x.get_size())

    new_size = list(x.get_size())

    zero_tensor = False
    for i in range(len(repeats)):
        if repeats[i] == 0:
            zero_tensor = True
        new_size[i] = new_size[i] * repeats[i]

    if zero_tensor:
        return empty(new_size, dtype=x.get_dtype(), device=x.get_device())
    if all((a == 1 or b == 1) for a, b in zip(repeats, old_size)):
        return clone(expand(x, new_size))

    x_loader: Callable[[Any], Any]

    def inner_fn(index):
        assert len(index) == len(repeats)
        index = list(index)
        for i in range(len(repeats)):
            if repeats[i] != 1:
                if old_size[i] == 1:
                    index[i] = sympy.S.Zero
                else:
                    index[i] = ModularIndexing(index[i], 1, old_size[i])
        return x_loader(index)

    # TODO Laith is there better check
    if not free_unbacked_symbols(old_size) and not free_unbacked_symbols(new_size):
        old_size_product = V.graph.sizevars.guarding_hint_or_throw(
            sympy_product(old_size)
        )
        if old_size_product > 0:
            # maybe realize the input but skip for unbacked symints since it'll
            # choke on the size hint.
            x.mark_reuse(
                V.graph.sizevars.guarding_hint_or_throw(sympy_product(new_size))
                // old_size_product
            )

    x_loader = x.make_loader()
    return Pointwise.create(
        device=x.get_device(),
        dtype=x.get_dtype(),
        inner_fn=inner_fn,
        ranges=list(new_size),
    )