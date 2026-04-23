def test_discretenb_degenerate_one_class_case(
    DiscreteNaiveBayes,
    use_partial_fit,
    train_on_single_class_y,
):
    # Most array attributes of a discrete naive Bayes classifier should have a
    # first-axis length equal to the number of classes. Exceptions include:
    # ComplementNB.feature_all_, CategoricalNB.n_categories_.
    # Confirm that this is the case for binary problems and the degenerate
    # case of a single class in the training set, when fitting with `fit` or
    # `partial_fit`.
    # Non-regression test for handling degenerate one-class case:
    # https://github.com/scikit-learn/scikit-learn/issues/18974

    X = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    y = [1, 1, 2]
    if train_on_single_class_y:
        X = X[:-1]
        y = y[:-1]
    classes = sorted(list(set(y)))
    num_classes = len(classes)

    clf = DiscreteNaiveBayes()
    if use_partial_fit:
        clf.partial_fit(X, y, classes=classes)
    else:
        clf.fit(X, y)
    assert clf.predict(X[:1]) == y[0]

    # Check that attributes have expected first-axis lengths
    attribute_names = [
        "classes_",
        "class_count_",
        "class_log_prior_",
        "feature_count_",
        "feature_log_prob_",
    ]
    for attribute_name in attribute_names:
        attribute = getattr(clf, attribute_name, None)
        if attribute is None:
            # CategoricalNB has no feature_count_ attribute
            continue
        if isinstance(attribute, np.ndarray):
            assert attribute.shape[0] == num_classes
        else:
            # CategoricalNB.feature_log_prob_ is a list of arrays
            for element in attribute:
                assert element.shape[0] == num_classes