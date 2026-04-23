def test_metaestimator_delegation():
    # Ensures specified metaestimators have methods iff subestimator does
    def hides(method):
        @property
        def wrapper(obj):
            if obj.hidden_method == method.__name__:
                raise AttributeError("%r is hidden" % obj.hidden_method)
            return functools.partial(method, obj)

        return wrapper

    class SubEstimator(BaseEstimator):
        def __init__(self, param=1, hidden_method=None):
            self.param = param
            self.hidden_method = hidden_method

        def fit(self, X, y=None, *args, **kwargs):
            self.coef_ = np.arange(X.shape[1])
            self.classes_ = []
            return True

        def _check_fit(self):
            check_is_fitted(self)

        @hides
        def inverse_transform(self, X, *args, **kwargs):
            self._check_fit()
            return X

        @hides
        def transform(self, X, *args, **kwargs):
            self._check_fit()
            return X

        @hides
        def predict(self, X, *args, **kwargs):
            self._check_fit()
            return np.ones(X.shape[0])

        @hides
        def predict_proba(self, X, *args, **kwargs):
            self._check_fit()
            return np.ones(X.shape[0])

        @hides
        def predict_log_proba(self, X, *args, **kwargs):
            self._check_fit()
            return np.ones(X.shape[0])

        @hides
        def decision_function(self, X, *args, **kwargs):
            self._check_fit()
            return np.ones(X.shape[0])

        @hides
        def score(self, X, y, *args, **kwargs):
            self._check_fit()
            return 1.0

    methods = [
        k
        for k in SubEstimator.__dict__.keys()
        if not k.startswith("_") and not k.startswith("fit")
    ]
    methods.sort()

    for delegator_data in DELEGATING_METAESTIMATORS:
        delegate = SubEstimator()
        delegator = delegator_data.construct(delegate)
        for method in methods:
            if method in delegator_data.skip_methods:
                continue
            assert hasattr(delegate, method)
            assert hasattr(delegator, method), (
                "%s does not have method %r when its delegate does"
                % (
                    delegator_data.name,
                    method,
                )
            )
            # delegation before fit raises a NotFittedError
            if method == "score":
                with pytest.raises(NotFittedError):
                    getattr(delegator, method)(
                        delegator_data.fit_args[0], delegator_data.fit_args[1]
                    )
            else:
                with pytest.raises(NotFittedError):
                    getattr(delegator, method)(delegator_data.fit_args[0])

        delegator.fit(*delegator_data.fit_args)
        for method in methods:
            if method in delegator_data.skip_methods:
                continue
            # smoke test delegation
            if method == "score":
                getattr(delegator, method)(
                    delegator_data.fit_args[0], delegator_data.fit_args[1]
                )
            else:
                getattr(delegator, method)(delegator_data.fit_args[0])

        for method in methods:
            if method in delegator_data.skip_methods:
                continue
            delegate = SubEstimator(hidden_method=method)
            delegator = delegator_data.construct(delegate)
            assert not hasattr(delegate, method)
            assert not hasattr(delegator, method), (
                "%s has method %r when its delegate does not"
                % (
                    delegator_data.name,
                    method,
                )
            )