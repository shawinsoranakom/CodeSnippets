def test_categorical_encoding_strategies():
    # Check native categorical handling vs different encoding strategies. We
    # make sure that native encoding needs only 1 split to achieve a perfect
    # prediction on a simple dataset. In contrast, OneHotEncoded data needs
    # more depth / splits, and treating categories as ordered (just using
    # OrdinalEncoder) requires even more depth.

    # dataset with one random continuous feature, and one categorical feature
    # with values in [0, 5], e.g. from an OrdinalEncoder.
    # class == 1 iff categorical value in {0, 2, 4}
    rng = np.random.RandomState(0)
    n_samples = 10_000
    f1 = rng.rand(n_samples)
    f2 = rng.randint(6, size=n_samples)
    X = np.c_[f1, f2]
    y = np.zeros(shape=n_samples)
    y[X[:, 1] % 2 == 0] = 1

    # make sure dataset is balanced so that the baseline_prediction doesn't
    # influence predictions too much with max_iter = 1
    assert 0.49 < y.mean() < 0.51

    native_cat_specs = [
        [False, True],
        [1],
    ]
    try:
        import pandas as pd

        X = pd.DataFrame(X, columns=["f_0", "f_1"])
        native_cat_specs.append(["f_1"])
    except ImportError:
        pass

    for native_cat_spec in native_cat_specs:
        clf_cat = HistGradientBoostingClassifier(
            max_iter=1, max_depth=1, categorical_features=native_cat_spec
        )
        clf_cat.fit(X, y)

        # Using native categorical encoding, we get perfect predictions with just
        # one split
        assert cross_val_score(clf_cat, X, y).mean() == 1

    # quick sanity check for the bitset: 0, 2, 4 = 2**0 + 2**2 + 2**4 = 21
    expected_left_bitset = [21, 0, 0, 0, 0, 0, 0, 0]
    left_bitset = clf_cat.fit(X, y)._predictors[0][0].raw_left_cat_bitsets[0]
    assert_array_equal(left_bitset, expected_left_bitset)

    # Treating categories as ordered, we need more depth / more splits to get
    # the same predictions
    clf_no_cat = HistGradientBoostingClassifier(
        max_iter=1, max_depth=4, categorical_features=None
    )
    assert cross_val_score(clf_no_cat, X, y).mean() < 0.9

    clf_no_cat.set_params(max_depth=5)
    assert cross_val_score(clf_no_cat, X, y).mean() == 1

    # Using OHEd data, we need less splits than with pure OEd data, but we
    # still need more splits than with the native categorical splits
    ct = make_column_transformer(
        (OneHotEncoder(sparse_output=False), [1]), remainder="passthrough"
    )
    X_ohe = ct.fit_transform(X)
    clf_no_cat.set_params(max_depth=2)
    assert cross_val_score(clf_no_cat, X_ohe, y).mean() < 0.9

    clf_no_cat.set_params(max_depth=3)
    assert cross_val_score(clf_no_cat, X_ohe, y).mean() == 1