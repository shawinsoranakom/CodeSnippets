def test_parameters_sampler_replacement():
    # raise warning if n_iter is bigger than total parameter space
    params = [
        {"first": [0, 1], "second": ["a", "b", "c"]},
        {"third": ["two", "values"]},
    ]
    sampler = ParameterSampler(params, n_iter=9)
    n_iter = 9
    grid_size = 8
    expected_warning = (
        "The total space of parameters %d is smaller "
        "than n_iter=%d. Running %d iterations. For "
        "exhaustive searches, use GridSearchCV." % (grid_size, n_iter, grid_size)
    )
    with pytest.warns(UserWarning, match=expected_warning):
        list(sampler)

    # degenerates to GridSearchCV if n_iter the same as grid_size
    sampler = ParameterSampler(params, n_iter=8)
    samples = list(sampler)
    assert len(samples) == 8
    for values in ParameterGrid(params):
        assert values in samples
    assert len(ParameterSampler(params, n_iter=1000)) == 8

    # test sampling without replacement in a large grid
    params = {"a": range(10), "b": range(10), "c": range(10)}
    sampler = ParameterSampler(params, n_iter=99, random_state=42)
    samples = list(sampler)
    assert len(samples) == 99
    hashable_samples = ["a%db%dc%d" % (p["a"], p["b"], p["c"]) for p in samples]
    assert len(set(hashable_samples)) == 99

    # doesn't go into infinite loops
    params_distribution = {"first": bernoulli(0.5), "second": ["a", "b", "c"]}
    sampler = ParameterSampler(params_distribution, n_iter=7)
    samples = list(sampler)
    assert len(samples) == 7