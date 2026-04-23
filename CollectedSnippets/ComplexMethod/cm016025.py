def test_integers_to_negative_integer_power(self):
        # Note that the combination of uint64 with a signed integer
        # has common type np.float64. The other combinations should all
        # raise a ValueError for integer ** negative integer.
        exp = [np.array(-1, dt)[()] for dt in "bhil"]

        # 1 ** -1 possible special case
        base = [np.array(1, dt)[()] for dt in "bhilB"]
        for i1, i2 in itertools.product(base, exp):
            if i1.dtype != np.uint64:
                assert_raises(ValueError, operator.pow, i1, i2)
            else:
                res = operator.pow(i1, i2)
                assert_(res.dtype.type is np.float64)
                assert_almost_equal(res, 1.0)

        # -1 ** -1 possible special case
        base = [np.array(-1, dt)[()] for dt in "bhil"]
        for i1, i2 in itertools.product(base, exp):
            if i1.dtype != np.uint64:
                assert_raises(ValueError, operator.pow, i1, i2)
            else:
                res = operator.pow(i1, i2)
                assert_(res.dtype.type is np.float64)
                assert_almost_equal(res, -1.0)

        # 2 ** -1 perhaps generic
        base = [np.array(2, dt)[()] for dt in "bhilB"]
        for i1, i2 in itertools.product(base, exp):
            if i1.dtype != np.uint64:
                assert_raises(ValueError, operator.pow, i1, i2)
            else:
                res = operator.pow(i1, i2)
                assert_(res.dtype.type is np.float64)
                assert_almost_equal(res, 0.5)