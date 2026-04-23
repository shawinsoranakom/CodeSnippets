def test_temperature_scaling(n_classes, ensemble):
    """Check temperature scaling calibration"""
    X, y = make_classification(
        n_samples=1000,
        n_features=10,
        n_informative=10,
        n_redundant=0,
        n_classes=n_classes,
        n_clusters_per_class=1,
        class_sep=2.0,
        random_state=42,
    )
    X_train, X_cal, y_train, y_cal = train_test_split(X, y, random_state=42)
    clf = LogisticRegression(C=np.inf, tol=1e-8, max_iter=200, random_state=0)
    clf.fit(X_train, y_train)
    # Train the calibrator on the calibrating set
    cal_clf = CalibratedClassifierCV(
        FrozenEstimator(clf), cv=3, method="temperature", ensemble=ensemble
    ).fit(X_cal, y_cal)

    calibrated_classifiers = cal_clf.calibrated_classifiers_

    for calibrated_classifier in calibrated_classifiers:
        # There is one and only one temperature scaling calibrator
        # for each calibrated classifier
        assert len(calibrated_classifier.calibrators) == 1

        calibrator = calibrated_classifier.calibrators[0]
        # Should not raise any error
        check_is_fitted(calibrator)
        # The optimal inverse temperature parameter should always be positive
        assert calibrator.beta_ > 0

    if not ensemble:
        # Accuracy score is invariant under temperature scaling
        y_pred = clf.predict(X_cal)
        y_pred_cal = cal_clf.predict(X_cal)
        assert accuracy_score(y_cal, y_pred_cal) == accuracy_score(y_cal, y_pred)

        # Log Loss should be improved on the calibrating set
        y_scores = clf.predict_proba(X_cal)
        y_scores_cal = cal_clf.predict_proba(X_cal)
        assert log_loss(y_cal, y_scores_cal) <= log_loss(y_cal, y_scores)

        # Refinement error should be invariant under temperature scaling.
        # Use ROC AUC as a proxy for refinement error. Also note that ROC AUC
        # itself is invariant under strict monotone transformations.
        if n_classes == 2:
            y_scores = y_scores[:, 1]
            y_scores_cal = y_scores_cal[:, 1]
        assert_allclose(
            roc_auc_score(y_cal, y_scores, multi_class="ovr"),
            roc_auc_score(y_cal, y_scores_cal, multi_class="ovr"),
        )

        # For Logistic Regression, the optimal temperature should be close to 1.0
        # on the training set.
        y_scores_train = clf.predict_proba(X_train)
        ts = _TemperatureScaling().fit(y_scores_train, y_train)
        assert_allclose(ts.beta_, 1.0, atol=1e-6, rtol=0)