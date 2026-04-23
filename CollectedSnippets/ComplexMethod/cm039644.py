def test_preprocess_copy_data_no_checks(sparse_container, to_copy, use_sample_weight):
    X, y = make_regression()
    X[X < 2.5] = 0.0

    sample_weight = np.ones(len(y)) if use_sample_weight else None

    if sparse_container is not None:
        X = sparse_container(X)

    X_, y_, _, _, _, _ = _preprocess_data(
        X,
        y,
        sample_weight=sample_weight,
        fit_intercept=True,
        copy=to_copy,
        check_input=False,
    )

    if sparse_container is not None:
        if to_copy or use_sample_weight:
            # sparse X, y always copied when use_sample_weight, regardless of to_copy
            assert not np.may_share_memory(X_.data, X.data)
        else:
            assert np.may_share_memory(X_.data, X.data)
    else:
        assert np.may_share_memory(X_, X) == (not to_copy)