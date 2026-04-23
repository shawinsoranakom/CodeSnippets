def test_kde_random(self):
        kde_random = statistics.kde_random
        StatisticsError = statistics.StatisticsError
        kernels = ['normal', 'gauss', 'logistic', 'sigmoid', 'rectangular',
                   'uniform', 'triangular', 'parabolic', 'epanechnikov',
                   'quartic', 'biweight', 'triweight', 'cosine']
        sample = [-2.1, -1.3, -0.4, 1.9, 5.1, 6.2]

        # Smoke test

        for kernel in kernels:
            with self.subTest(kernel=kernel):
                rand = kde_random(sample, h=1.5, kernel=kernel)
                selections = [rand() for i in range(10)]

        # Check error cases

        with self.assertRaises(StatisticsError):
            kde_random([], h=1.0)                       # Empty dataset
        with self.assertRaises(TypeError):
            kde_random(['abc', 'def'], 1.5)             # Non-numeric data
        with self.assertRaises(TypeError):
            kde_random(iter(sample), 1.5)               # Data is not a sequence
        with self.assertRaises(StatisticsError):
            kde_random(sample, h=-1.0)                  # Zero bandwidth
        with self.assertRaises(StatisticsError):
            kde_random(sample, h=0.0)                   # Negative bandwidth
        with self.assertRaises(TypeError):
            kde_random(sample, h='str')                 # Wrong bandwidth type
        with self.assertRaises(StatisticsError):
            kde_random(sample, h=1.0, kernel='bogus')   # Invalid kernel

        # Test name and docstring of the generated function

        h = 1.5
        kernel = 'cosine'
        rand = kde_random(sample, h, kernel)
        self.assertEqual(rand.__name__, 'rand')
        self.assertIn(kernel, rand.__doc__)
        self.assertIn(repr(h), rand.__doc__)

        # Approximate distribution test: Compare a random sample to the expected distribution

        data = [-2.1, -1.3, -0.4, 1.9, 5.1, 6.2, 7.8, 14.3, 15.1, 15.3, 15.8, 17.0]
        xarr = [x / 10 for x in range(-100, 250)]
        n = 1_000_000
        h = 1.75
        dx = 0.1

        def p_observed(x):
            # P(x <= X < x+dx)
            i = bisect.bisect_left(big_sample, x)
            j = bisect.bisect_left(big_sample, x + dx)
            return (j - i) / len(big_sample)

        def p_expected(x):
            # P(x <= X < x+dx)
            return F_hat(x + dx) - F_hat(x)

        for kernel in kernels:
            with self.subTest(kernel=kernel):

                rand = kde_random(data, h, kernel, seed=8675309**2)
                big_sample = sorted([rand() for i in range(n)])
                F_hat = statistics.kde(data, h, kernel, cumulative=True)

                for x in xarr:
                    self.assertTrue(math.isclose(p_observed(x), p_expected(x), abs_tol=0.0005))

        # Test online updates to data

        data = [1, 2]
        rand = kde_random(data, 5, 'triangular')
        self.assertLess(max([rand() for i in range(5000)]), 10)
        data.append(100)
        self.assertGreater(max(rand() for i in range(5000)), 10)