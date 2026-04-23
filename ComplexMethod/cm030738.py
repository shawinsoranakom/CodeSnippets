def test_mtestfile(self):
        fail_fmt = "{}: {}({!r}): {}"

        failures = []
        for id, fn, arg, expected, flags in parse_mtestfile(math_testcases):
            func = getattr(math, fn)

            if 'invalid' in flags or 'divide-by-zero' in flags:
                expected = 'ValueError'
            elif 'overflow' in flags:
                expected = 'OverflowError'

            try:
                got = func(arg)
            except ValueError:
                got = 'ValueError'
            except OverflowError:
                got = 'OverflowError'

            # Default tolerances
            ulp_tol, abs_tol = 5, 0.0

            # Exceptions to the defaults
            if fn == 'gamma':
                # Experimental results on one platform gave
                # an accuracy of <= 10 ulps across the entire float
                # domain. We weaken that to require 20 ulp accuracy.
                ulp_tol = 20

            elif fn == 'lgamma':
                # we use a weaker accuracy test for lgamma;
                # lgamma only achieves an absolute error of
                # a few multiples of the machine accuracy, in
                # general.
                abs_tol = 1e-15

            elif fn == 'erfc' and arg >= 0.0:
                # erfc has less-than-ideal accuracy for large
                # arguments (x ~ 25 or so), mainly due to the
                # error involved in computing exp(-x*x).
                #
                # Observed between CPython and mpmath at 25 dp:
                #       x <  0 : err <= 2 ulp
                #  0 <= x <  1 : err <= 10 ulp
                #  1 <= x < 10 : err <= 100 ulp
                # 10 <= x < 20 : err <= 300 ulp
                # 20 <= x      : < 600 ulp
                #
                if arg < 1.0:
                    ulp_tol = 10
                elif arg < 10.0:
                    ulp_tol = 100
                else:
                    ulp_tol = 1000

            failure = result_check(expected, got, ulp_tol, abs_tol)
            if failure is None:
                continue

            msg = fail_fmt.format(id, fn, arg, failure)
            failures.append(msg)

        if failures:
            self.fail('Failures in test_mtestfile:\n  ' +
                      '\n  '.join(failures))