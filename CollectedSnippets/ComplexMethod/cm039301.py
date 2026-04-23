def test_sparse_random_matrix():
    # Check some statical properties of sparse random matrix
    n_components = 100
    n_features = 500

    for density in [0.3, 1.0]:
        s = 1 / density

        A = _sparse_random_matrix(
            n_components, n_features, density=density, random_state=0
        )
        A = densify(A)

        # Check possible values
        values = np.unique(A)
        assert np.sqrt(s) / np.sqrt(n_components) in values
        assert -np.sqrt(s) / np.sqrt(n_components) in values

        if density == 1.0:
            assert np.size(values) == 2
        else:
            assert 0.0 in values
            assert np.size(values) == 3

        # Check that the random matrix follow the proper distribution.
        # Let's say that each element of a_{ij} of A is taken from
        #
        # - -sqrt(s) / sqrt(n_components)   with probability 1 / 2s
        # -  0                              with probability 1 - 1 / s
        # - +sqrt(s) / sqrt(n_components)   with probability 1 / 2s
        #
        assert_almost_equal(np.mean(A == 0.0), 1 - 1 / s, decimal=2)
        assert_almost_equal(
            np.mean(A == np.sqrt(s) / np.sqrt(n_components)), 1 / (2 * s), decimal=2
        )
        assert_almost_equal(
            np.mean(A == -np.sqrt(s) / np.sqrt(n_components)), 1 / (2 * s), decimal=2
        )

        assert_almost_equal(np.var(A == 0.0, ddof=1), (1 - 1 / s) * 1 / s, decimal=2)
        assert_almost_equal(
            np.var(A == np.sqrt(s) / np.sqrt(n_components), ddof=1),
            (1 - 1 / (2 * s)) * 1 / (2 * s),
            decimal=2,
        )
        assert_almost_equal(
            np.var(A == -np.sqrt(s) / np.sqrt(n_components), ddof=1),
            (1 - 1 / (2 * s)) * 1 / (2 * s),
            decimal=2,
        )