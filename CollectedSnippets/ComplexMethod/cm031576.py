def tern_close_numbers(prec, emax, emin, itr):
    if itr is None:
        itr = 1000
    for _ in range(itr):
        for func1 in close_funcs:
            for func2 in close_funcs:
                for func3 in close_funcs:
                    yield (func1(prec, emax, emin), func2(prec, emax, emin),
                           func3(prec, emax, emin))
        for func in close_funcs:
            yield (randdec(prec, emax), func(prec, emax, emin),
                   func(prec, emax, emin))
            yield (func(prec, emax, emin), randdec(prec, emax),
                   func(prec, emax, emin))
            yield (func(prec, emax, emin), func(prec, emax, emin),
                   randdec(prec, emax))
        for func in close_funcs:
            yield (randdec(prec, emax), randdec(prec, emax),
                   func(prec, emax, emin))
            yield (randdec(prec, emax), func(prec, emax, emin),
                   randdec(prec, emax))
            yield (func(prec, emax, emin), randdec(prec, emax),
                   randdec(prec, emax))