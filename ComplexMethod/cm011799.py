def expand(x, sizes):
    (x,) = promote_constants([x])
    if isinstance(x, ir.BaseConstant):
        return ExpandView.create(x, tuple(sizes))
    assert isinstance(x, TensorBox)
    assert isinstance(sizes, (list, tuple))
    if tuple(x.get_size()) == tuple(sizes):
        return x

    if not free_unbacked_symbols(x.get_size()):
        x_size_product = V.graph.sizevars.guarding_hint_or_throw(
            sympy_product(x.get_size())
        )
        # TODO: It would be better to realize the input if any of its sizes
        # are unbacked, because typically the size will be non-zero.  However,
        # this cannot be done directly as below as we'll choke on the size_hint
        # here
        if x_size_product > 0 and not free_unbacked_symbols(sizes):
            # maybe realize input before broadcasting it
            x.mark_reuse(
                V.graph.sizevars.guarding_hint_or_throw(sympy_product(sizes))
                // x_size_product
            )
    return TensorBox(ExpandView.create(x.data, tuple(sizes)))