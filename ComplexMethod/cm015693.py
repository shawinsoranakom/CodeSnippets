def test_range_iterators(self):
        # exercise 'fast' iterators, that use a rangeiterobject internally.
        # see issue 7298
        limits = [base + jiggle
                  for M in (2**32, 2**64)
                  for base in (-M, -M//2, 0, M//2, M)
                  for jiggle in (-2, -1, 0, 1, 2)]
        test_ranges = [(start, end, step)
                       for start in limits
                       for end in limits
                       for step in (-2**63, -2**31, -2, -1, 1, 2)]
        test_ranges += [(-2**63, 2**63-2, 1)] # regression test for gh-100810

        for start, end, step in test_ranges:
            iter1 = range(start, end, step)
            iter2 = pyrange(start, end, step)
            test_id = "range({}, {}, {})".format(start, end, step)
            # check first 100 entries
            self.assert_iterators_equal(iter1, iter2, test_id, limit=100)

            iter1 = reversed(range(start, end, step))
            iter2 = pyrange_reversed(start, end, step)
            test_id = "reversed(range({}, {}, {}))".format(start, end, step)
            self.assert_iterators_equal(iter1, iter2, test_id, limit=100)