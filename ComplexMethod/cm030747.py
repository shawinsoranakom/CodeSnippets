def test_cmath_matches_math(self):
        # check that corresponding cmath and math functions are equal
        # for floats in the appropriate range

        # test_values in (0, 1)
        test_values = [0.01, 0.1, 0.2, 0.5, 0.9, 0.99]

        # test_values for functions defined on [-1., 1.]
        unit_interval = test_values + [-x for x in test_values] + \
            [0., 1., -1.]

        # test_values for log, log10, sqrt
        positive = test_values + [1.] + [1./x for x in test_values]
        nonnegative = [0.] + positive

        # test_values for functions defined on the whole real line
        real_line = [0.] + positive + [-x for x in positive]

        test_functions = {
            'acos' : unit_interval,
            'asin' : unit_interval,
            'atan' : real_line,
            'cos' : real_line,
            'cosh' : real_line,
            'exp' : real_line,
            'log' : positive,
            'log10' : positive,
            'sin' : real_line,
            'sinh' : real_line,
            'sqrt' : nonnegative,
            'tan' : real_line,
            'tanh' : real_line}

        for fn, values in test_functions.items():
            float_fn = getattr(math, fn)
            complex_fn = getattr(cmath, fn)
            for v in values:
                z = complex_fn(v)
                self.rAssertAlmostEqual(float_fn(v), z.real)
                self.assertEqual(0., z.imag)

        # test two-argument version of log with various bases
        for base in [0.5, 2., 10.]:
            for v in positive:
                z = cmath.log(v, base)
                self.rAssertAlmostEqual(math.log(v, base), z.real)
                self.assertEqual(0., z.imag)