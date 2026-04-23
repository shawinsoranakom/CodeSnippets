def test_spectral_biclustering(global_random_seed, csr_container):
    # Test Kluger methods on a checkerboard dataset.
    S, rows, cols = make_checkerboard(
        (30, 30), 3, noise=0.5, random_state=global_random_seed
    )

    non_default_params = {
        "method": ["scale", "log"],
        "svd_method": ["arpack"],
        "n_svd_vecs": [20],
        "mini_batch": [True],
    }

    for mat in (S, csr_container(S)):
        for param_name, param_values in non_default_params.items():
            for param_value in param_values:
                model = SpectralBiclustering(
                    n_clusters=3,
                    n_init=3,
                    init="k-means++",
                    random_state=global_random_seed,
                )
                model.set_params(**dict([(param_name, param_value)]))

                if issparse(mat) and model.get_params().get("method") == "log":
                    # cannot take log of sparse matrix
                    with pytest.raises(ValueError):
                        model.fit(mat)
                    continue
                else:
                    model.fit(mat)

                assert model.rows_.shape == (9, 30)
                assert model.columns_.shape == (9, 30)
                assert_array_equal(model.rows_.sum(axis=0), np.repeat(3, 30))
                assert_array_equal(model.columns_.sum(axis=0), np.repeat(3, 30))
                assert consensus_score(model.biclusters_, (rows, cols)) == 1

                _test_shape_indices(model)