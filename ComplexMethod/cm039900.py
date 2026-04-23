def check_classifiers_train(
    name, classifier_orig, readonly_memmap=False, X_dtype="float64"
):
    X_m, y_m = make_blobs(n_samples=300, random_state=0)
    X_m = X_m.astype(X_dtype)
    X_m, y_m = shuffle(X_m, y_m, random_state=7)
    X_m = StandardScaler().fit_transform(X_m)
    # generate binary problem from multi-class one
    y_b = y_m[y_m != 2]
    X_b = X_m[y_m != 2]

    if name in ["BernoulliNB", "MultinomialNB", "ComplementNB", "CategoricalNB"]:
        X_m -= X_m.min()
        X_b -= X_b.min()

    if readonly_memmap:
        X_m, y_m, X_b, y_b = create_memmap_backed_data([X_m, y_m, X_b, y_b])

    problems = [(X_b, y_b)]
    tags = get_tags(classifier_orig)
    if tags.classifier_tags.multi_class:
        problems.append((X_m, y_m))

    for X, y in problems:
        classes = np.unique(y)
        n_classes = len(classes)
        n_samples, n_features = X.shape
        classifier = clone(classifier_orig)
        X = _enforce_estimator_tags_X(classifier, X)
        y = _enforce_estimator_tags_y(classifier, y)

        set_random_state(classifier)
        # raises error on malformed input for fit
        if not tags.no_validation:
            with raises(
                ValueError,
                err_msg=(
                    f"The classifier {name} does not raise an error when "
                    "incorrect/malformed input data for fit is passed. The number "
                    "of training examples is not the same as the number of "
                    "labels. Perhaps use check_X_y in fit."
                ),
            ):
                classifier.fit(X, y[:-1])

        # fit
        classifier.fit(X, y)
        # with lists
        classifier.fit(X.tolist(), y.tolist())
        assert hasattr(classifier, "classes_")
        y_pred = classifier.predict(X)

        assert y_pred.shape == (n_samples,)
        # training set performance
        if not tags.classifier_tags.poor_score:
            assert accuracy_score(y, y_pred) > 0.83

        # raises error on malformed input for predict
        msg_pairwise = (
            "The classifier {} does not raise an error when shape of X in "
            " {} is not equal to (n_test_samples, n_training_samples)"
        )
        msg = (
            "The classifier {} does not raise an error when the number of "
            "features in {} is different from the number of features in "
            "fit."
        )

        if not tags.no_validation:
            if tags.input_tags.pairwise:
                with raises(
                    ValueError,
                    err_msg=msg_pairwise.format(name, "predict"),
                ):
                    classifier.predict(X.reshape(-1, 1))
            else:
                with raises(ValueError, err_msg=msg.format(name, "predict")):
                    classifier.predict(X.T)
        if hasattr(classifier, "decision_function"):
            try:
                # decision_function agrees with predict
                decision = classifier.decision_function(X)
                if n_classes == 2:
                    if tags.target_tags.single_output:
                        assert decision.shape == (n_samples,)
                    else:
                        assert decision.shape == (n_samples, 1)
                    dec_pred = (decision.ravel() > 0).astype(int)
                    assert_array_equal(dec_pred, y_pred)
                else:
                    assert decision.shape == (n_samples, n_classes)
                    assert_array_equal(np.argmax(decision, axis=1), y_pred)

                # raises error on malformed input for decision_function
                if not tags.no_validation:
                    if tags.input_tags.pairwise:
                        with raises(
                            ValueError,
                            err_msg=msg_pairwise.format(name, "decision_function"),
                        ):
                            classifier.decision_function(X.reshape(-1, 1))
                    else:
                        with raises(
                            ValueError,
                            err_msg=msg.format(name, "decision_function"),
                        ):
                            classifier.decision_function(X.T)
            except NotImplementedError:
                pass

        if hasattr(classifier, "predict_proba"):
            # predict_proba agrees with predict
            y_prob = classifier.predict_proba(X)
            assert y_prob.shape == (n_samples, n_classes)
            assert_array_equal(np.argmax(y_prob, axis=1), y_pred)
            # check that probas for all classes sum to one
            assert_array_almost_equal(np.sum(y_prob, axis=1), np.ones(n_samples))
            if not tags.no_validation:
                # raises error on malformed input for predict_proba
                if tags.input_tags.pairwise:
                    with raises(
                        ValueError,
                        err_msg=msg_pairwise.format(name, "predict_proba"),
                    ):
                        classifier.predict_proba(X.reshape(-1, 1))
                else:
                    with raises(
                        ValueError,
                        err_msg=msg.format(name, "predict_proba"),
                    ):
                        classifier.predict_proba(X.T)
            if hasattr(classifier, "predict_log_proba"):
                # predict_log_proba is a transformation of predict_proba
                y_log_prob = classifier.predict_log_proba(X)
                assert_allclose(y_log_prob, np.log(y_prob), 8, atol=1e-9)
                assert_array_equal(np.argsort(y_log_prob), np.argsort(y_prob))