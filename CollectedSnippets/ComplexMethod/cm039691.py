def test_base_estimator_inputs(Est):
    # make sure that the base estimators are passed the correct parameters and
    # number of samples at each iteration.
    pd = pytest.importorskip("pandas")

    passed_n_samples_fit = []
    passed_n_samples_predict = []
    passed_params = []

    class FastClassifierBookKeeping(FastClassifier):
        def fit(self, X, y):
            passed_n_samples_fit.append(X.shape[0])
            return super().fit(X, y)

        def predict(self, X):
            passed_n_samples_predict.append(X.shape[0])
            return super().predict(X)

        def set_params(self, **params):
            passed_params.append(params)
            return super().set_params(**params)

    n_samples = 1024
    n_splits = 2
    X, y = make_classification(n_samples=n_samples, random_state=0)
    param_grid = {"a": ("l1", "l2"), "b": list(range(30))}
    base_estimator = FastClassifierBookKeeping()

    sh = Est(
        base_estimator,
        param_grid,
        factor=2,
        cv=n_splits,
        return_train_score=False,
        refit=False,
    )
    if Est is HalvingRandomSearchCV:
        # same number of candidates as with the grid
        sh.set_params(n_candidates=2 * 30, min_resources="exhaust")

    sh.fit(X, y)

    assert len(passed_n_samples_fit) == len(passed_n_samples_predict)
    passed_n_samples = [
        x + y for (x, y) in zip(passed_n_samples_fit, passed_n_samples_predict)
    ]

    # Lists are of length n_splits * n_iter * n_candidates_at_i.
    # Each chunk of size n_splits corresponds to the n_splits folds for the
    # same candidate at the same iteration, so they contain equal values. We
    # subsample such that the lists are of length n_iter * n_candidates_at_it
    passed_n_samples = passed_n_samples[::n_splits]
    passed_params = passed_params[::n_splits]

    cv_results_df = pd.DataFrame(sh.cv_results_)

    assert len(passed_params) == len(passed_n_samples) == len(cv_results_df)

    uniques, counts = np.unique(passed_n_samples, return_counts=True)
    assert (sh.n_resources_ == uniques).all()
    assert (sh.n_candidates_ == counts).all()

    assert (cv_results_df["params"] == passed_params).all()
    assert (cv_results_df["n_resources"] == passed_n_samples).all()