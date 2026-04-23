def test_isin(self, kind):
        def _isin_slow(a, b):
            b = np.asarray(b).flatten().tolist()
            return a in b

        isin_slow = np.vectorize(_isin_slow, otypes=[bool], excluded={1})

        def assert_isin_equal(a, b):
            x = np.isin(a, b, kind=kind)
            y = isin_slow(a, b)
            assert_array_equal(x, y)

        # multidimensional arrays in both arguments
        a = np.arange(24).reshape([2, 3, 4])
        b = np.array([[10, 20, 30], [0, 1, 3], [11, 22, 33]])
        assert_isin_equal(a, b)

        # array-likes as both arguments
        c = [(9, 8), (7, 6)]
        d = (9, 7)
        assert_isin_equal(c, d)

        # zero-d array:
        f = np.array(3)
        assert_isin_equal(f, b)
        assert_isin_equal(a, f)
        assert_isin_equal(f, f)

        # scalar:
        assert_isin_equal(5, b)
        assert_isin_equal(a, 6)
        assert_isin_equal(5, 6)

        # empty array-like:
        if kind != "table":
            # An empty list will become float64,
            # which is invalid for kind="table"
            x = []
            assert_isin_equal(x, b)
            assert_isin_equal(a, x)
            assert_isin_equal(x, x)

        # empty array with various types:
        for dtype in [bool, np.int64, np.float64]:
            if kind == "table" and dtype == np.float64:
                continue

            if dtype in {np.int64, np.float64}:
                ar = np.array([10, 20, 30], dtype=dtype)
            elif dtype is bool:
                ar = np.array([True, False, False])

            empty_array = np.array([], dtype=dtype)

            assert_isin_equal(empty_array, ar)
            assert_isin_equal(ar, empty_array)
            assert_isin_equal(empty_array, empty_array)

        # we use two different sizes for the b array here to test the
        # two different paths in isin().
        for mult in (1, 10):
            # One check without np.array to make sure lists are handled correct
            a = [5, 7, 1, 2]
            b = [2, 4, 3, 1, 5] * mult
            ec = np.array([True, False, True, True])
            c = isin(a, b, assume_unique=True, kind=kind)
            assert_array_equal(c, ec)

            a[0] = 8
            ec = np.array([False, False, True, True])
            c = isin(a, b, assume_unique=True, kind=kind)
            assert_array_equal(c, ec)

            a[0], a[3] = 4, 8
            ec = np.array([True, False, True, False])
            c = isin(a, b, assume_unique=True, kind=kind)
            assert_array_equal(c, ec)

            a = np.array([5, 4, 5, 3, 4, 4, 3, 4, 3, 5, 2, 1, 5, 5])
            b = [2, 3, 4] * mult
            ec = [
                False,
                True,
                False,
                True,
                True,
                True,
                True,
                True,
                True,
                False,
                True,
                False,
                False,
                False,
            ]
            c = isin(a, b, kind=kind)
            assert_array_equal(c, ec)

            b = b + [5, 5, 4] * mult
            ec = [
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                False,
                True,
                True,
            ]
            c = isin(a, b, kind=kind)
            assert_array_equal(c, ec)

            a = np.array([5, 7, 1, 2])
            b = np.array([2, 4, 3, 1, 5] * mult)
            ec = np.array([True, False, True, True])
            c = isin(a, b, kind=kind)
            assert_array_equal(c, ec)

            a = np.array([5, 7, 1, 1, 2])
            b = np.array([2, 4, 3, 3, 1, 5] * mult)
            ec = np.array([True, False, True, True, True])
            c = isin(a, b, kind=kind)
            assert_array_equal(c, ec)

            a = np.array([5, 5])
            b = np.array([2, 2] * mult)
            ec = np.array([False, False])
            c = isin(a, b, kind=kind)
            assert_array_equal(c, ec)

        a = np.array([5])
        b = np.array([2])
        ec = np.array([False])
        c = isin(a, b, kind=kind)
        assert_array_equal(c, ec)

        if kind in {None, "sort"}:
            assert_array_equal(isin([], [], kind=kind), [])