def test_compute_log_det_cholesky(global_dtype):
    n_features = 2
    rand_data = RandomData(np.random.RandomState(0), dtype=global_dtype)

    for covar_type in COVARIANCE_TYPE:
        covariance = rand_data.covariances[covar_type]

        if covar_type == "full":
            predected_det = np.array([linalg.det(cov) for cov in covariance])
        elif covar_type == "tied":
            predected_det = linalg.det(covariance)
        elif covar_type == "diag":
            predected_det = np.array([np.prod(cov) for cov in covariance])
        elif covar_type == "spherical":
            predected_det = covariance**n_features

        # We compute the cholesky decomposition of the covariance matrix
        assert covariance.dtype == global_dtype
        expected_det = _compute_log_det_cholesky(
            _compute_precision_cholesky(covariance, covar_type),
            covar_type,
            n_features=n_features,
        )
        assert_array_almost_equal(expected_det, -0.5 * np.log(predected_det))
        assert expected_det.dtype == global_dtype