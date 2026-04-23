def test_multioutput(Tree, criterion):
    # Check estimators on multi-output problems.
    X = [
        [-2, -1],
        [-1, -1],
        [-1, -2],
        [1, 1],
        [1, 2],
        [2, 1],
        [-2, 1],
        [-1, 1],
        [-1, 2],
        [2, -1],
        [1, -1],
        [1, -2],
    ]

    y = np.array(
        [
            [-1, 0],
            [-1, 0],
            [-1, 0],
            [1, 1],
            [1, 1],
            [1, 1],
            [-1, 2],
            [-1, 2],
            [-1, 2],
            [1, 3],
            [1, 3],
            [1, 3],
        ]
    )

    T = [[-1, -1], [1, 1], [-1, 1], [1, -1]]
    y_true = np.array([[-1, 0], [1, 1], [-1, 2], [1, 3]])

    is_clf = criterion in CLF_CRITERIONS
    if criterion == "poisson":
        # poisson doesn't support negative y, and ignores null y.
        y[y <= 0] += 4
        y_true[y_true <= 0] += 4

    if is_clf:
        # toy classification problem
        clf = Tree(random_state=0, criterion=criterion)
        y_hat = clf.fit(X, y).predict(T)
        assert_array_equal(y_hat, y_true)
        assert y_hat.shape == (4, 2)

        proba = clf.predict_proba(T)
        assert len(proba) == 2
        assert proba[0].shape == (4, 2)
        assert proba[1].shape == (4, 4)

        log_proba = clf.predict_log_proba(T)
        assert len(log_proba) == 2
        assert log_proba[0].shape == (4, 2)
        assert log_proba[1].shape == (4, 4)
    else:
        # toy regression problem
        reg = Tree(random_state=0, criterion=criterion)
        y_hat = reg.fit(X, y).predict(T)
        assert_almost_equal(y_hat, y_true)
        assert y_hat.shape == (4, 2)