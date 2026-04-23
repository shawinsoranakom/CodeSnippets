def _check_pos_label_statistics(
    display_class, response_method, constructor_name, check_metric
):
    """Test switching `pos_label` gives correct statistics, using imbalanced data."""
    X, y = load_breast_cancer(return_X_y=True)
    # create highly imbalanced classes
    idx_positive = np.flatnonzero(y == 1)
    idx_negative = np.flatnonzero(y == 0)
    idx_selected = np.hstack([idx_negative, idx_positive[:25]])
    X, y = X[idx_selected], y[idx_selected]
    X, y = shuffle(X, y, random_state=42)
    # only use 2 features to make the problem even harder
    X = X[:, :2]
    y = np.array(["cancer" if c == 1 else "not cancer" for c in y], dtype=object)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        stratify=y,
        random_state=0,
    )

    classifier = LogisticRegression()
    classifier.fit(X_train, y_train)
    cv_results = cross_validate(
        LogisticRegression(), X, y, cv=3, return_estimator=True, return_indices=True
    )

    # Sanity check to be sure the positive class is `classes_[0]`.
    # Class imbalance ensures a large difference in prediction values between classes,
    # allowing us to catch errors when we switch `pos_label`.
    assert classifier.classes_.tolist() == ["cancer", "not cancer"]

    y_score = getattr(classifier, response_method)(X_test)
    # we select the corresponding probability columns or reverse the decision
    # function otherwise
    y_score_cancer = -1 * y_score if y_score.ndim == 1 else y_score[:, 0]
    y_score_not_cancer = y_score if y_score.ndim == 1 else y_score[:, 1]

    pos_label = "cancer"
    y_score = y_score_cancer
    if constructor_name == "from_estimator":
        display = display_class.from_estimator(
            classifier,
            X_test,
            y_test,
            pos_label=pos_label,
            response_method=response_method,
        )
    elif constructor_name == "from_predictions":
        display = display_class.from_predictions(
            y_test,
            y_score,
            pos_label=pos_label,
        )
    else:  # constructor_name = "from_cv_results"
        display = display_class.from_cv_results(
            cv_results,
            X,
            y,
            response_method=response_method,
            pos_label=pos_label,
        )

    check_metric(display, constructor_name, pos_label)

    pos_label = "not cancer"
    y_score = y_score_not_cancer
    if constructor_name == "from_estimator":
        display = display_class.from_estimator(
            classifier,
            X_test,
            y_test,
            response_method=response_method,
            pos_label=pos_label,
        )
    elif constructor_name == "from_predictions":
        display = display_class.from_predictions(
            y_test,
            y_score,
            pos_label=pos_label,
        )
    else:  # constructor_name = "from_cv_results"
        display = display_class.from_cv_results(
            cv_results,
            X,
            y,
            response_method=response_method,
            pos_label=pos_label,
        )

    check_metric(display, constructor_name, pos_label)