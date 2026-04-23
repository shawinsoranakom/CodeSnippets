def test_pca_solver_equivalence(
    other_svd_solver,
    data_shape,
    rank_deficient,
    whiten,
    global_random_seed,
    global_dtype,
):
    if data_shape == "tall":
        n_samples, n_features = 100, 30
    else:
        n_samples, n_features = 30, 100
    n_samples_test = 10

    if rank_deficient:
        rng = np.random.default_rng(global_random_seed)
        rank = min(n_samples, n_features) // 2
        X = rng.standard_normal(
            size=(n_samples + n_samples_test, rank)
        ) @ rng.standard_normal(size=(rank, n_features))
    else:
        X = make_low_rank_matrix(
            n_samples=n_samples + n_samples_test,
            n_features=n_features,
            tail_strength=0.5,
            random_state=global_random_seed,
        )
        # With a non-zero tail strength, the data is actually full-rank.
        rank = min(n_samples, n_features)

    X = X.astype(global_dtype, copy=False)
    X_train, X_test = X[:n_samples], X[n_samples:]

    if global_dtype == np.float32:
        tols = dict(atol=3e-2, rtol=1e-5)
        variance_threshold = 1e-5
    else:
        tols = dict(atol=1e-10, rtol=1e-12)
        variance_threshold = 1e-12

    extra_other_kwargs = {}
    if other_svd_solver == "randomized":
        # Only check for a truncated result with a large number of iterations
        # to make sure that we can recover precise results.
        n_components = 10
        extra_other_kwargs = {"iterated_power": 50}
    elif other_svd_solver == "arpack":
        # Test all components except the last one which cannot be estimated by
        # arpack.
        n_components = np.minimum(n_samples, n_features) - 1
    else:
        # Test all components to high precision.
        n_components = None

    pca_full = PCA(n_components=n_components, svd_solver="full", whiten=whiten)
    pca_other = PCA(
        n_components=n_components,
        svd_solver=other_svd_solver,
        whiten=whiten,
        random_state=global_random_seed,
        **extra_other_kwargs,
    )
    X_trans_full_train = pca_full.fit_transform(X_train)
    assert np.isfinite(X_trans_full_train).all()
    assert X_trans_full_train.dtype == global_dtype
    X_trans_other_train = pca_other.fit_transform(X_train)
    assert np.isfinite(X_trans_other_train).all()
    assert X_trans_other_train.dtype == global_dtype

    assert (pca_full.explained_variance_ >= 0).all()
    assert_allclose(pca_full.explained_variance_, pca_other.explained_variance_, **tols)
    assert_allclose(
        pca_full.explained_variance_ratio_,
        pca_other.explained_variance_ratio_,
        **tols,
    )
    reference_components = pca_full.components_
    assert np.isfinite(reference_components).all()
    other_components = pca_other.components_
    assert np.isfinite(other_components).all()

    # For some choice of n_components and data distribution, some components
    # might be pure noise, let's ignore them in the comparison:
    stable = pca_full.explained_variance_ > variance_threshold
    assert stable.sum() > 1
    assert_allclose(reference_components[stable], other_components[stable], **tols)

    # As a result the output of fit_transform should be the same:
    assert_allclose(
        X_trans_other_train[:, stable], X_trans_full_train[:, stable], **tols
    )

    # And similarly for the output of transform on new data (except for the
    # last component that can be underdetermined):
    X_trans_full_test = pca_full.transform(X_test)
    assert np.isfinite(X_trans_full_test).all()
    assert X_trans_full_test.dtype == global_dtype
    X_trans_other_test = pca_other.transform(X_test)
    assert np.isfinite(X_trans_other_test).all()
    assert X_trans_other_test.dtype == global_dtype
    assert_allclose(X_trans_other_test[:, stable], X_trans_full_test[:, stable], **tols)

    # Check that inverse transform reconstructions for both solvers are
    # compatible.
    X_recons_full_test = pca_full.inverse_transform(X_trans_full_test)
    assert np.isfinite(X_recons_full_test).all()
    assert X_recons_full_test.dtype == global_dtype
    X_recons_other_test = pca_other.inverse_transform(X_trans_other_test)
    assert np.isfinite(X_recons_other_test).all()
    assert X_recons_other_test.dtype == global_dtype

    if pca_full.components_.shape[0] == pca_full.components_.shape[1]:
        # In this case, the models should have learned the same invertible
        # transform. They should therefore both be able to reconstruct the test
        # data.
        assert_allclose(X_recons_full_test, X_test, **tols)
        assert_allclose(X_recons_other_test, X_test, **tols)
    elif pca_full.components_.shape[0] < rank:
        # In the absence of noisy components, both models should be able to
        # reconstruct the same low-rank approximation of the original data.
        assert pca_full.explained_variance_.min() > variance_threshold
        assert_allclose(X_recons_full_test, X_recons_other_test, **tols)
    else:
        # When n_features > n_samples and n_components is larger than the rank
        # of the training set, the output of the `inverse_transform` function
        # is ill-defined. We can only check that we reach the same fixed point
        # after another round of transform:
        assert_allclose(
            pca_full.transform(X_recons_full_test)[:, stable],
            pca_other.transform(X_recons_other_test)[:, stable],
            **tols,
        )