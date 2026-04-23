def test_multinomial_logistic_regression_string_inputs():
    """Test internally encode labels"""
    n_samples, n_features, n_classes = 50, 5, 3
    X_ref, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_classes=n_classes,
        n_informative=3,
        random_state=0,
    )
    y_str = LabelEncoder().fit(["bar", "baz", "foo"]).inverse_transform(y)
    # For numerical labels, let y values be taken from set (-1, 0, 1)
    y = np.array(y) - 1
    # Test for string labels
    lr = LogisticRegression()
    lr_cv = LogisticRegressionCV(
        Cs=3,
        use_legacy_attributes=False,
        scoring="neg_log_loss",  # TODO(1.11): remove because it is default now
    )
    lr_str = LogisticRegression()
    lr_cv_str = LogisticRegressionCV(
        Cs=3,
        use_legacy_attributes=False,
        scoring="neg_log_loss",  # TODO(1.11): remove because it is default now
    )

    lr.fit(X_ref, y)
    lr_cv.fit(X_ref, y)
    lr_str.fit(X_ref, y_str)
    lr_cv_str.fit(X_ref, y_str)

    assert_allclose(lr.coef_, lr_str.coef_)
    assert_allclose(lr.predict_proba(X_ref), lr_str.predict_proba(X_ref))
    assert sorted(lr_str.classes_) == ["bar", "baz", "foo"]
    assert_allclose(lr_cv.coef_, lr_cv_str.coef_)
    assert_allclose(lr_cv.predict_proba(X_ref), lr_cv_str.predict_proba(X_ref))
    assert sorted(lr_str.classes_) == ["bar", "baz", "foo"]
    assert sorted(lr_cv_str.classes_) == ["bar", "baz", "foo"]

    # The predictions should be in original labels
    assert sorted(np.unique(lr_str.predict(X_ref))) == ["bar", "baz", "foo"]
    # CV does not necessarily predict all labels
    assert set(np.unique(lr_cv_str.predict(X_ref))) <= {"bar", "baz", "foo"}

    # We use explicit Cs parameter to make sure all labels are predicted for each C.
    lr_cv_str = LogisticRegressionCV(
        Cs=[1, 2, 10],
        use_legacy_attributes=False,
        scoring="neg_log_loss",  # TODO(1.11): remove because it is default now
    ).fit(X_ref, y_str)
    assert sorted(np.unique(lr_cv_str.predict(X_ref))) == ["bar", "baz", "foo"]

    # Make sure class weights can be given with string labels
    lr_cv_str = LogisticRegression(class_weight={"bar": 1, "baz": 2, "foo": 0}).fit(
        X_ref, y_str
    )

    assert sorted(np.unique(lr_cv_str.predict(X_ref))) == ["bar", "baz"]