def test_aggressive_elimination(
    Est,
    aggressive_elimination,
    max_resources,
    expected_n_iterations,
    expected_n_required_iterations,
    expected_n_possible_iterations,
    expected_n_remaining_candidates,
    expected_n_candidates,
    expected_n_resources,
):
    # Test the aggressive_elimination parameter.

    n_samples = 1000
    X, y = make_classification(n_samples=n_samples, random_state=0)
    param_grid = {"a": ("l1", "l2"), "b": list(range(30))}
    base_estimator = FastClassifier()

    if max_resources == "limited":
        max_resources = 180
    else:
        max_resources = n_samples

    sh = Est(
        base_estimator,
        param_grid,
        aggressive_elimination=aggressive_elimination,
        max_resources=max_resources,
        factor=3,
    )
    sh.set_params(verbose=True)  # just for test coverage

    if Est is HalvingRandomSearchCV:
        # same number of candidates as with the grid
        sh.set_params(n_candidates=2 * 30, min_resources="exhaust")

    sh.fit(X, y)

    assert sh.n_iterations_ == expected_n_iterations
    assert sh.n_required_iterations_ == expected_n_required_iterations
    assert sh.n_possible_iterations_ == expected_n_possible_iterations
    assert sh.n_resources_ == expected_n_resources
    assert sh.n_candidates_ == expected_n_candidates
    assert sh.n_remaining_candidates_ == expected_n_remaining_candidates
    assert ceil(sh.n_candidates_[-1] / sh.factor) == sh.n_remaining_candidates_