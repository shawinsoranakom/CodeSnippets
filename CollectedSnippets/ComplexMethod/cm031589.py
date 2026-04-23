def test_format(method, prec, exp_range, restricted_range, itr, stat):
    """Iterate the __format__ method through many test cases."""
    for op in all_unary(prec, exp_range, itr):
        fmt1 = rand_format(chr(random.randrange(0, 128)), 'EeGgn')
        fmt2 = rand_locale()
        for fmt in (fmt1, fmt2):
            fmtop = (op[0], fmt)
            t = TestSet(method, fmtop)
            try:
                if not convert(t, convstr=False):
                    continue
                callfuncs(t)
                verify(t, stat)
            except VerifyError as err:
                log(err)
    for op in all_unary(prec, 9999, itr):
        fmt1 = rand_format(chr(random.randrange(0, 128)), 'Ff%')
        fmt2 = rand_locale()
        for fmt in (fmt1, fmt2):
            fmtop = (op[0], fmt)
            t = TestSet(method, fmtop)
            try:
                if not convert(t, convstr=False):
                    continue
                callfuncs(t)
                verify(t, stat)
            except VerifyError as err:
                log(err)