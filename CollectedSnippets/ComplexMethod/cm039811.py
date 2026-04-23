def test_sample():
    rng = np.random.RandomState(0)
    rand_data = RandomData(rng, scale=7, n_components=3)
    n_features, n_components = rand_data.n_features, rand_data.n_components

    for covar_type in COVARIANCE_TYPE:
        X = rand_data.X[covar_type]

        gmm = GaussianMixture(
            n_components=n_components, covariance_type=covar_type, random_state=rng
        )
        # To sample we need that GaussianMixture is fitted
        msg = "This GaussianMixture instance is not fitted"
        with pytest.raises(NotFittedError, match=msg):
            gmm.sample(0)
        gmm.fit(X)

        msg = "Invalid value for 'n_samples'"
        with pytest.raises(ValueError, match=msg):
            gmm.sample(0)

        # Just to make sure the class samples correctly
        n_samples = 20000
        X_s, y_s = gmm.sample(n_samples)

        for k in range(n_components):
            if covar_type == "full":
                assert_array_almost_equal(
                    gmm.covariances_[k], np.cov(X_s[y_s == k].T), decimal=1
                )
            elif covar_type == "tied":
                assert_array_almost_equal(
                    gmm.covariances_, np.cov(X_s[y_s == k].T), decimal=1
                )
            elif covar_type == "diag":
                assert_array_almost_equal(
                    gmm.covariances_[k], np.diag(np.cov(X_s[y_s == k].T)), decimal=1
                )
            else:
                assert_array_almost_equal(
                    gmm.covariances_[k],
                    np.var(X_s[y_s == k] - gmm.means_[k]),
                    decimal=1,
                )

        means_s = np.array([np.mean(X_s[y_s == k], 0) for k in range(n_components)])
        assert_array_almost_equal(gmm.means_, means_s, decimal=1)

        # Check shapes of sampled data, see
        # https://github.com/scikit-learn/scikit-learn/issues/7701
        assert X_s.shape == (n_samples, n_features)

        for sample_size in range(1, 100):
            X_s, _ = gmm.sample(sample_size)
            assert X_s.shape == (sample_size, n_features)