def test_column_transformer_named_estimators():
    X_array = np.array([[0.0, 1.0, 2.0], [2.0, 4.0, 6.0]]).T
    ct = ColumnTransformer(
        [
            ("trans1", StandardScaler(), [0]),
            ("trans2", StandardScaler(with_std=False), [1]),
        ]
    )
    assert not hasattr(ct, "transformers_")
    ct.fit(X_array)
    assert hasattr(ct, "transformers_")
    assert isinstance(ct.named_transformers_["trans1"], StandardScaler)
    assert isinstance(ct.named_transformers_.trans1, StandardScaler)
    assert isinstance(ct.named_transformers_["trans2"], StandardScaler)
    assert isinstance(ct.named_transformers_.trans2, StandardScaler)
    assert not ct.named_transformers_.trans2.with_std
    # check it are fitted transformers
    assert ct.named_transformers_.trans1.mean_ == 1.0