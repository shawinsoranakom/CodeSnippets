def bin_random_mixed_op(prec, emax, emin, itr=None):
    if itr is None:
        itr = 1000
    for _ in range(itr):
        for func in number_funcs:
            yield randdec(prec, emax), func()
            yield func(), randdec(prec, emax)
        for number in number_funcs:
            for dec in close_funcs:
                yield dec(prec, emax, emin), number()
    # Test garbage input
    for x in (['x'], ('y',), {'z'}, {1:'z'}):
        for y in (['x'], ('y',), {'z'}, {1:'z'}):
            yield x, y