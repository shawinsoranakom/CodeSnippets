def test_min_max_resources(
    Est,
    min_resources,
    max_resources,
    expected_n_iterations,
    expected_n_possible_iterations,
    expected_n_resources,
):
    # Test the min_resources and max_resources parameters, and how they affect
    # the number of resources used at each iteration
    n_samples = 1000
    X, y = make_classification(n_samples=n_samples, random_state=0)
    param_grid = {"a": [1, 2], "b": [1, 2, 3]}
    base_estimator = FastClassifier()

    sh = Est(
        base_estimator,
        param_grid,
        factor=3,
        min_resources=min_resources,
        max_resources=max_resources,
    )
    if Est is HalvingRandomSearchCV:
        sh.set_params(n_candidates=6)  # same number as with the grid

    sh.fit(X, y)

    expected_n_required_iterations = 2  # given 6 combinations and factor = 3
    assert sh.n_iterations_ == expected_n_iterations
    assert sh.n_required_iterations_ == expected_n_required_iterations
    assert sh.n_possible_iterations_ == expected_n_possible_iterations
    assert sh.n_resources_ == expected_n_resources
    if min_resources == "exhaust":
        assert sh.n_possible_iterations_ == sh.n_iterations_ == len(sh.n_resources_)