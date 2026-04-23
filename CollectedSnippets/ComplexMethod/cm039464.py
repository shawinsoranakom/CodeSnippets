def test_set_random_states():
    # Linear Discriminant Analysis doesn't have random state: smoke test
    _set_random_states(LinearDiscriminantAnalysis(), random_state=17)

    clf1 = Perceptron(random_state=None)
    assert clf1.random_state is None
    # check random_state is None still sets
    _set_random_states(clf1, None)
    assert isinstance(clf1.random_state, int)

    # check random_state fixes results in consistent initialisation
    _set_random_states(clf1, 3)
    assert isinstance(clf1.random_state, int)
    clf2 = Perceptron(random_state=None)
    _set_random_states(clf2, 3)
    assert clf1.random_state == clf2.random_state

    # nested random_state

    def make_steps():
        return [
            ("sel", SelectFromModel(Perceptron(random_state=None))),
            ("clf", Perceptron(random_state=None)),
        ]

    est1 = Pipeline(make_steps())
    _set_random_states(est1, 3)
    assert isinstance(est1.steps[0][1].estimator.random_state, int)
    assert isinstance(est1.steps[1][1].random_state, int)
    assert (
        est1.get_params()["sel__estimator__random_state"]
        != est1.get_params()["clf__random_state"]
    )

    # ensure multiple random_state parameters are invariant to get_params()
    # iteration order

    class AlphaParamPipeline(Pipeline):
        def get_params(self, *args, **kwargs):
            params = Pipeline.get_params(self, *args, **kwargs).items()
            return OrderedDict(sorted(params))

    class RevParamPipeline(Pipeline):
        def get_params(self, *args, **kwargs):
            params = Pipeline.get_params(self, *args, **kwargs).items()
            return OrderedDict(sorted(params, reverse=True))

    for cls in [AlphaParamPipeline, RevParamPipeline]:
        est2 = cls(make_steps())
        _set_random_states(est2, 3)
        assert (
            est1.get_params()["sel__estimator__random_state"]
            == est2.get_params()["sel__estimator__random_state"]
        )
        assert (
            est1.get_params()["clf__random_state"]
            == est2.get_params()["clf__random_state"]
        )