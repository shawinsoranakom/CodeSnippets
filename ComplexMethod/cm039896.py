def _check_transformer(name, transformer_orig, X, y):
    n_samples, n_features = np.asarray(X).shape
    transformer = clone(transformer_orig)
    set_random_state(transformer)

    # fit

    if name in CROSS_DECOMPOSITION:
        y_ = np.c_[np.asarray(y), np.asarray(y)]
        y_[::2, 1] *= 2
        if isinstance(X, _NotAnArray):
            y_ = _NotAnArray(y_)
    else:
        y_ = y

    transformer.fit(X, y_)
    # fit_transform method should work on non fitted estimator
    transformer_clone = clone(transformer)
    X_pred = transformer_clone.fit_transform(X, y=y_)

    if isinstance(X_pred, tuple):
        for x_pred in X_pred:
            assert x_pred.shape[0] == n_samples
    else:
        # check for consistent n_samples
        assert X_pred.shape[0] == n_samples

    if hasattr(transformer, "transform"):
        if name in CROSS_DECOMPOSITION:
            X_pred2 = transformer.transform(X, y_)
            X_pred3 = transformer.fit_transform(X, y=y_)
        else:
            X_pred2 = transformer.transform(X)
            X_pred3 = transformer.fit_transform(X, y=y_)

        if get_tags(transformer_orig).non_deterministic:
            msg = name + " is non deterministic"
            raise SkipTest(msg)
        if isinstance(X_pred, tuple) and isinstance(X_pred2, tuple):
            for x_pred, x_pred2, x_pred3 in zip(X_pred, X_pred2, X_pred3):
                assert_allclose_dense_sparse(
                    x_pred,
                    x_pred2,
                    atol=1e-2,
                    err_msg="fit_transform and transform outcomes not consistent in %s"
                    % transformer,
                )
                assert_allclose_dense_sparse(
                    x_pred,
                    x_pred3,
                    atol=1e-2,
                    err_msg="consecutive fit_transform outcomes not consistent in %s"
                    % transformer,
                )
        else:
            assert_allclose_dense_sparse(
                X_pred,
                X_pred2,
                err_msg="fit_transform and transform outcomes not consistent in %s"
                % transformer,
                atol=1e-2,
            )
            assert_allclose_dense_sparse(
                X_pred,
                X_pred3,
                atol=1e-2,
                err_msg="consecutive fit_transform outcomes not consistent in %s"
                % transformer,
            )
            assert _num_samples(X_pred2) == n_samples
            assert _num_samples(X_pred3) == n_samples

        # raises error on malformed input for transform
        if (
            hasattr(X, "shape")
            and get_tags(transformer).requires_fit
            and X.ndim == 2
            and X.shape[1] > 1
        ):
            # If it's not an array, it does not have a 'T' property
            with raises(
                ValueError,
                err_msg=(
                    f"The transformer {name} does not raise an error "
                    "when the number of features in transform is different from "
                    "the number of features in fit."
                ),
            ):
                transformer.transform(X[:, :-1])