def test_affinities(global_random_seed):
    # Note: in the following, random_state has been selected to have
    # a dataset that yields a stable eigen decomposition both when built
    # on OSX and Linux
    X, y = make_blobs(
        n_samples=20, random_state=0, centers=[[1, 1], [-1, -1]], cluster_std=0.01
    )
    # nearest neighbors affinity
    sp = SpectralClustering(n_clusters=2, affinity="nearest_neighbors", random_state=0)
    with pytest.warns(UserWarning, match="not fully connected"):
        sp.fit(X)
    assert adjusted_rand_score(y, sp.labels_) == 1

    sp = SpectralClustering(n_clusters=2, gamma=2, random_state=global_random_seed)
    labels = sp.fit(X).labels_
    assert adjusted_rand_score(y, labels) == 1

    X = check_random_state(10).rand(10, 5) * 10

    kernels_available = kernel_metrics()
    for kern in kernels_available:
        # Additive chi^2 gives a negative similarity matrix which
        # doesn't make sense for spectral clustering
        if kern != "additive_chi2":
            sp = SpectralClustering(n_clusters=2, affinity=kern, random_state=0)
            labels = sp.fit(X).labels_
            assert (X.shape[0],) == labels.shape

    sp = SpectralClustering(n_clusters=2, affinity=lambda x, y: 1, random_state=0)
    labels = sp.fit(X).labels_
    assert (X.shape[0],) == labels.shape

    def histogram(x, y, **kwargs):
        # Histogram kernel implemented as a callable.
        assert kwargs == {}  # no kernel_params that we didn't ask for
        return np.minimum(x, y).sum()

    sp = SpectralClustering(n_clusters=2, affinity=histogram, random_state=0)
    labels = sp.fit(X).labels_
    assert (X.shape[0],) == labels.shape