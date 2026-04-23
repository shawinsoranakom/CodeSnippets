def test_one_hot_encoder_drop_manual(missing_value):
    cats_to_drop = ["def", 12, 3, 56, missing_value]
    enc = OneHotEncoder(drop=cats_to_drop)
    X = [
        ["abc", 12, 2, 55, "a"],
        ["def", 12, 1, 55, "a"],
        ["def", 12, 3, 56, missing_value],
    ]
    trans = enc.fit_transform(X).toarray()
    exp = [[1, 0, 1, 1, 1], [0, 1, 0, 1, 1], [0, 0, 0, 0, 0]]
    assert_array_equal(trans, exp)
    assert enc.drop is cats_to_drop

    dropped_cats = [
        cat[feature] for cat, feature in zip(enc.categories_, enc.drop_idx_)
    ]
    X_inv_trans = enc.inverse_transform(trans)
    X_array = np.array(X, dtype=object)

    # last value is np.nan
    if is_scalar_nan(cats_to_drop[-1]):
        assert_array_equal(dropped_cats[:-1], cats_to_drop[:-1])
        assert is_scalar_nan(dropped_cats[-1])
        assert is_scalar_nan(cats_to_drop[-1])
        # do not include the last column which includes missing values
        assert_array_equal(X_array[:, :-1], X_inv_trans[:, :-1])

        # check last column is the missing value
        assert_array_equal(X_array[-1, :-1], X_inv_trans[-1, :-1])
        assert is_scalar_nan(X_array[-1, -1])
        assert is_scalar_nan(X_inv_trans[-1, -1])
    else:
        assert_array_equal(dropped_cats, cats_to_drop)
        assert_array_equal(X_array, X_inv_trans)