def test_means_for_all_inits(init_params, global_random_seed, global_dtype):
    # Check fitted means properties for all initializations
    rng = np.random.RandomState(global_random_seed)
    rand_data = RandomData(rng, scale=5, dtype=global_dtype)
    n_components = rand_data.n_components
    X = rand_data.X["full"]

    gmm = GaussianMixture(
        n_components=n_components, init_params=init_params, random_state=rng
    )
    gmm.fit(X)

    assert gmm.means_.shape == (n_components, X.shape[1])
    assert np.all(X.min(axis=0) <= gmm.means_)
    assert np.all(gmm.means_ <= X.max(axis=0))
    assert gmm.converged_
    assert gmm.means_.dtype == global_dtype
    assert gmm.covariances_.dtype == global_dtype
    assert gmm.weights_.dtype == global_dtype