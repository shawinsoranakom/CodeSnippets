def check_transformer_get_feature_names_out(name, transformer_orig):
    tags = get_tags(transformer_orig)
    if not tags.input_tags.two_d_array or tags.no_validation:
        return

    X, y = make_blobs(
        n_samples=30,
        centers=[[0, 0, 0], [1, 1, 1]],
        random_state=0,
        n_features=2,
        cluster_std=0.1,
    )
    X = StandardScaler().fit_transform(X)

    transformer = clone(transformer_orig)
    X = _enforce_estimator_tags_X(transformer, X)

    n_features = X.shape[1]
    set_random_state(transformer)

    y_ = y
    if name in CROSS_DECOMPOSITION:
        y_ = np.c_[np.asarray(y), np.asarray(y)]
        y_[::2, 1] *= 2

    X_transform = transformer.fit_transform(X, y=y_)
    input_features = [f"feature{i}" for i in range(n_features)]

    # input_features names is not the same length as n_features_in_
    with raises(ValueError, match="input_features should have length equal"):
        transformer.get_feature_names_out(input_features[::2])

    feature_names_out = transformer.get_feature_names_out(input_features)
    assert feature_names_out is not None
    assert isinstance(feature_names_out, np.ndarray)
    assert feature_names_out.dtype == object
    assert all(isinstance(name, str) for name in feature_names_out)

    if isinstance(X_transform, tuple):
        n_features_out = X_transform[0].shape[1]
    else:
        n_features_out = X_transform.shape[1]

    assert len(feature_names_out) == n_features_out, (
        f"Expected {n_features_out} feature names, got {len(feature_names_out)}"
    )