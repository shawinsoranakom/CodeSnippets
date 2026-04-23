def test_gaussian_mixture_fit(global_dtype):
    # recover the ground truth
    rng = np.random.RandomState(0)
    rand_data = RandomData(rng, dtype=global_dtype)
    n_features = rand_data.n_features
    n_components = rand_data.n_components

    for covar_type in COVARIANCE_TYPE:
        X = rand_data.X[covar_type]
        g = GaussianMixture(
            n_components=n_components,
            n_init=20,
            reg_covar=0,
            random_state=rng,
            covariance_type=covar_type,
        )
        g.fit(X)

        # needs more data to pass the test with rtol=1e-7
        assert_allclose(
            np.sort(g.weights_), np.sort(rand_data.weights), rtol=0.1, atol=1e-2
        )

        arg_idx1 = g.means_[:, 0].argsort()
        arg_idx2 = rand_data.means[:, 0].argsort()
        assert_allclose(
            g.means_[arg_idx1], rand_data.means[arg_idx2], rtol=0.1, atol=1e-2
        )

        if covar_type == "full":
            prec_pred = g.precisions_
            prec_test = rand_data.precisions["full"]
        elif covar_type == "tied":
            prec_pred = np.array([g.precisions_] * n_components)
            prec_test = np.array([rand_data.precisions["tied"]] * n_components)
        elif covar_type == "spherical":
            prec_pred = np.array([np.eye(n_features) * c for c in g.precisions_])
            prec_test = np.array(
                [np.eye(n_features) * c for c in rand_data.precisions["spherical"]]
            )
        elif covar_type == "diag":
            prec_pred = np.array([np.diag(d) for d in g.precisions_])
            prec_test = np.array([np.diag(d) for d in rand_data.precisions["diag"]])

        arg_idx1 = np.trace(prec_pred, axis1=1, axis2=2).argsort()
        arg_idx2 = np.trace(prec_test, axis1=1, axis2=2).argsort()
        for k, h in zip(arg_idx1, arg_idx2):
            ecov = EmpiricalCovariance()
            ecov.covariance_ = prec_test[h]
            # the accuracy depends on the number of data and randomness, rng
            assert_allclose(ecov.error_norm(prec_pred[k]), 0, atol=0.15)

        assert g.means_.dtype == global_dtype
        assert g.covariances_.dtype == global_dtype
        assert g.precisions_.dtype == global_dtype