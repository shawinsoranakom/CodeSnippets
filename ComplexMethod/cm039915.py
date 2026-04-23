def check_transformer_get_feature_names_out_pandas(name, transformer_orig):
    try:
        import pandas as pd
    except ImportError:
        raise SkipTest(
            "pandas is not installed: not checking column name consistency for pandas"
        )

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

    feature_names_in = [f"col{i}" for i in range(n_features)]
    df = pd.DataFrame(X, columns=feature_names_in, copy=False)
    X_transform = transformer.fit_transform(df, y=y_)

    # error is raised when `input_features` do not match feature_names_in
    invalid_feature_names = [f"bad{i}" for i in range(n_features)]
    with raises(ValueError, match="input_features is not equal to feature_names_in_"):
        transformer.get_feature_names_out(invalid_feature_names)

    feature_names_out_default = transformer.get_feature_names_out()
    feature_names_in_explicit_names = transformer.get_feature_names_out(
        feature_names_in
    )
    assert_array_equal(feature_names_out_default, feature_names_in_explicit_names)

    if isinstance(X_transform, tuple):
        n_features_out = X_transform[0].shape[1]
    else:
        n_features_out = X_transform.shape[1]

    assert len(feature_names_out_default) == n_features_out, (
        f"Expected {n_features_out} feature names, got {len(feature_names_out_default)}"
    )