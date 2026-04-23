def test_unary(method, prec, exp_range, restricted_range, itr, stat):
    """Iterate a unary function through many test cases."""
    if method in UnaryRestricted:
        exp_range = restricted_range
    for op in all_unary(prec, exp_range, itr):
        t = TestSet(method, op)
        try:
            if not convert(t):
                continue
            callfuncs(t)
            verify(t, stat)
        except VerifyError as err:
            log(err)

    if not method.startswith('__'):
        for op in unary_optarg(prec, exp_range, itr):
            t = TestSet(method, op)
            try:
                if not convert(t):
                    continue
                callfuncs(t)
                verify(t, stat)
            except VerifyError as err:
                log(err)