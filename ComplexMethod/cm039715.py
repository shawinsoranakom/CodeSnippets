def test_param_sampler():
    # test basic properties of param sampler
    param_distributions = {"kernel": ["rbf", "linear"], "C": uniform(0, 1)}
    sampler = ParameterSampler(
        param_distributions=param_distributions, n_iter=10, random_state=0
    )
    samples = [x for x in sampler]
    assert len(samples) == 10
    for sample in samples:
        assert sample["kernel"] in ["rbf", "linear"]
        assert 0 <= sample["C"] <= 1

    # test that repeated calls yield identical parameters
    param_distributions = {"C": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
    sampler = ParameterSampler(
        param_distributions=param_distributions, n_iter=3, random_state=0
    )
    assert [x for x in sampler] == [x for x in sampler]

    param_distributions = {"C": uniform(0, 1)}
    sampler = ParameterSampler(
        param_distributions=param_distributions, n_iter=10, random_state=0
    )
    assert [x for x in sampler] == [x for x in sampler]