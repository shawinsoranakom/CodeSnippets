def test_binary(method, prec, exp_range, restricted_range, itr, stat):
    """Iterate a binary function through many test cases."""
    if method in BinaryRestricted:
        exp_range = restricted_range
    for op in all_binary(prec, exp_range, itr):
        t = TestSet(method, op)
        try:
            if not convert(t):
                continue
            callfuncs(t)
            verify(t, stat)
        except VerifyError as err:
            log(err)

    if not method.startswith('__'):
        for op in binary_optarg(prec, exp_range, itr):
            t = TestSet(method, op)
            try:
                if not convert(t):
                    continue
                callfuncs(t)
                verify(t, stat)
            except VerifyError as err:
                log(err)