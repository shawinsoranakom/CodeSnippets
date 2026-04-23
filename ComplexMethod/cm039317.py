def test_ovo_decision_function():
    n_samples = iris.data.shape[0]

    ovo_clf = OneVsOneClassifier(LinearSVC(random_state=0))
    # first binary
    ovo_clf.fit(iris.data, iris.target == 0)
    decisions = ovo_clf.decision_function(iris.data)
    assert decisions.shape == (n_samples,)

    # then multi-class
    ovo_clf.fit(iris.data, iris.target)
    decisions = ovo_clf.decision_function(iris.data)

    assert decisions.shape == (n_samples, n_classes)
    assert_array_equal(decisions.argmax(axis=1), ovo_clf.predict(iris.data))

    # Compute the votes
    votes = np.zeros((n_samples, n_classes))

    k = 0
    for i in range(n_classes):
        for j in range(i + 1, n_classes):
            pred = ovo_clf.estimators_[k].predict(iris.data)
            votes[pred == 0, i] += 1
            votes[pred == 1, j] += 1
            k += 1

    # Extract votes and verify
    assert_array_equal(votes, np.round(decisions))

    for class_idx in range(n_classes):
        # For each sample and each class, there only 3 possible vote levels
        # because they are only 3 distinct class pairs thus 3 distinct
        # binary classifiers.
        # Therefore, sorting predictions based on votes would yield
        # mostly tied predictions:
        assert set(votes[:, class_idx]).issubset(set([0.0, 1.0, 2.0]))

        # The OVO decision function on the other hand is able to resolve
        # most of the ties on this data as it combines both the vote counts
        # and the aggregated confidence levels of the binary classifiers
        # to compute the aggregate decision function. The iris dataset
        # has 150 samples with a couple of duplicates. The OvO decisions
        # can resolve most of the ties:
        assert len(np.unique(decisions[:, class_idx])) > 146