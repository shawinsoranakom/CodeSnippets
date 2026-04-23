def test_permutation_score(coo_container):
    iris = load_iris()
    X = iris.data
    X_sparse = coo_container(X)
    y = iris.target
    svm = SVC(kernel="linear")
    cv = StratifiedKFold(2)

    score, scores, pvalue = permutation_test_score(
        svm, X, y, n_permutations=30, cv=cv, scoring="accuracy"
    )
    assert score > 0.9
    assert_almost_equal(pvalue, 0.0, 1)

    score_group, _, pvalue_group = permutation_test_score(
        svm,
        X,
        y,
        n_permutations=30,
        cv=cv,
        scoring="accuracy",
        groups=np.ones(y.size),
        random_state=0,
    )
    assert score_group == score
    assert pvalue_group == pvalue

    # check that we obtain the same results with a sparse representation
    svm_sparse = SVC(kernel="linear")
    cv_sparse = StratifiedKFold(2)
    score_group, _, pvalue_group = permutation_test_score(
        svm_sparse,
        X_sparse,
        y,
        n_permutations=30,
        cv=cv_sparse,
        scoring="accuracy",
        groups=np.ones(y.size),
        random_state=0,
    )

    assert score_group == score
    assert pvalue_group == pvalue

    # test with custom scoring object
    def custom_score(y_true, y_pred):
        return ((y_true == y_pred).sum() - (y_true != y_pred).sum()) / y_true.shape[0]

    scorer = make_scorer(custom_score)
    score, _, pvalue = permutation_test_score(
        svm, X, y, n_permutations=100, scoring=scorer, cv=cv, random_state=0
    )
    assert_almost_equal(score, 0.93, 2)
    assert_almost_equal(pvalue, 0.01, 3)

    # set random y
    y = np.mod(np.arange(len(y)), 3)

    score, scores, pvalue = permutation_test_score(
        svm, X, y, n_permutations=30, cv=cv, scoring="accuracy"
    )

    assert score < 0.5
    assert pvalue > 0.2