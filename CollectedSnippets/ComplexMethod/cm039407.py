def test_kernel_density_sampling(n_samples=100, n_features=3):
    rng = np.random.RandomState(0)
    X = rng.randn(n_samples, n_features)

    bandwidth = 0.2

    for kernel in ["gaussian", "tophat"]:
        # draw a tophat sample
        kde = KernelDensity(bandwidth=bandwidth, kernel=kernel).fit(X)
        samp = kde.sample(100)
        assert X.shape == samp.shape

        # check that samples are in the right range
        nbrs = NearestNeighbors(n_neighbors=1).fit(X)
        dist, ind = nbrs.kneighbors(X, return_distance=True)

        if kernel == "tophat":
            assert np.all(dist < bandwidth)
        elif kernel == "gaussian":
            # 5 standard deviations is safe for 100 samples, but there's a
            # very small chance this test could fail.
            assert np.all(dist < 5 * bandwidth)

    # check unsupported kernels
    for kernel in ["epanechnikov", "exponential", "linear", "cosine"]:
        kde = KernelDensity(bandwidth=bandwidth, kernel=kernel).fit(X)
        with pytest.raises(NotImplementedError):
            kde.sample(100)

    # non-regression test: used to return a scalar
    X = rng.randn(4, 1)
    kde = KernelDensity(kernel="gaussian").fit(X)
    assert kde.sample().shape == (1, 1)