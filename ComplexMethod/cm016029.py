def test_axis(self):
        # Vector norms.
        # Compare the use of `axis` with computing the norm of each row
        # or column separately.
        A = array([[1, 2, 3], [4, 5, 6]], dtype=self.dt)
        for order in [None, -1, 0, 1, 2, 3, np.inf, -np.inf]:
            expected0 = [norm(A[:, k], ord=order) for k in range(A.shape[1])]
            assert_almost_equal(norm(A, ord=order, axis=0), expected0)
            expected1 = [norm(A[k, :], ord=order) for k in range(A.shape[0])]
            assert_almost_equal(norm(A, ord=order, axis=1), expected1)

        # Matrix norms.
        B = np.arange(1, 25, dtype=self.dt).reshape(2, 3, 4)
        nd = B.ndim
        for order in [None, -2, 2, -1, 1, np.inf, -np.inf, "fro"]:
            for axis in itertools.combinations(range(-nd, nd), 2):
                row_axis, col_axis = axis
                if row_axis < 0:
                    row_axis += nd
                if col_axis < 0:
                    col_axis += nd
                if row_axis == col_axis:
                    assert_raises(
                        (RuntimeError, ValueError), norm, B, ord=order, axis=axis
                    )
                else:
                    n = norm(B, ord=order, axis=axis)

                    # The logic using k_index only works for nd = 3.
                    # This has to be changed if nd is increased.
                    k_index = nd - (row_axis + col_axis)
                    if row_axis < col_axis:
                        expected = [
                            norm(B[:].take(k, axis=k_index), ord=order)
                            for k in range(B.shape[k_index])
                        ]
                    else:
                        expected = [
                            norm(B[:].take(k, axis=k_index).T, ord=order)
                            for k in range(B.shape[k_index])
                        ]
                    assert_almost_equal(n, expected)