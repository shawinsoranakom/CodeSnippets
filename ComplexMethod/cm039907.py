def check_parameters_default_constructible(name, estimator_orig):
    # test default-constructibility
    # get rid of deprecation warnings

    Estimator = estimator_orig.__class__
    estimator = clone(estimator_orig)

    with ignore_warnings(category=FutureWarning):
        # test that set_params returns self
        # TODO(devtools): this should be a separate check.
        assert estimator.set_params() is estimator

        # test if init does nothing but set parameters
        # this is important for grid_search etc.
        # We get the default parameters from init and then
        # compare these against the actual values of the attributes.

        init = estimator.__init__

        try:

            def param_default_value(p):
                """Identify hyper parameters of an estimator."""
                return (
                    p.name != "self"
                    and p.kind != p.VAR_KEYWORD
                    and p.kind != p.VAR_POSITIONAL
                    # and it should have a default value for this test
                    and p.default != p.empty
                )

            def param_required(p):
                """Identify hyper parameters of an estimator."""
                return (
                    p.name != "self"
                    and p.kind != p.VAR_KEYWORD
                    # technically VAR_POSITIONAL is also required, but we don't have a
                    # nice way to check for it. We assume there's no VAR_POSITIONAL in
                    # the constructor parameters.
                    #
                    # TODO(devtools): separately check that the constructor doesn't
                    # have *args.
                    and p.kind != p.VAR_POSITIONAL
                    # these are parameters that don't have a default value and are
                    # required to construct the estimator.
                    and p.default == p.empty
                )

            required_params_names = [
                p.name for p in signature(init).parameters.values() if param_required(p)
            ]

            default_value_params = [
                p for p in signature(init).parameters.values() if param_default_value(p)
            ]

        except (TypeError, ValueError):
            # init is not a python function.
            # true for mixins
            return

        # here we construct an instance of the estimator using only the required
        # parameters.
        old_params = estimator.get_params()
        init_params = {
            param: old_params[param]
            for param in old_params
            if param in required_params_names
        }
        estimator = Estimator(**init_params)
        params = estimator.get_params()

        for init_param in default_value_params:
            allowed_types = {
                str,
                int,
                float,
                bool,
                tuple,
                type(None),
                type,
            }
            # Any numpy numeric such as np.int32.
            allowed_types.update(np.sctypeDict.values())

            allowed_value = (
                type(init_param.default) in allowed_types
                or
                # Although callables are mutable, we accept them as argument
                # default value and trust that neither the implementation of
                # the callable nor of the estimator changes the state of the
                # callable.
                callable(init_param.default)
            )

            assert allowed_value, (
                f"Parameter '{init_param.name}' of estimator "
                f"'{Estimator.__name__}' is of type "
                f"{type(init_param.default).__name__} which is not allowed. "
                f"'{init_param.name}' must be a callable or must be of type "
                f"{set(type.__name__ for type in allowed_types)}."
            )
            if init_param.name not in params.keys():
                # deprecated parameter, not in get_params
                assert init_param.default is None, (
                    f"Estimator parameter '{init_param.name}' of estimator "
                    f"'{Estimator.__name__}' is not returned by get_params. "
                    "If it is deprecated, set its default value to None."
                )
                continue

            param_value = params[init_param.name]
            if isinstance(param_value, np.ndarray):
                assert_array_equal(param_value, init_param.default)
            else:
                failure_text = (
                    f"Parameter {init_param.name} was mutated on init. All "
                    "parameters must be stored unchanged."
                )
                if is_scalar_nan(param_value):
                    # Allows to set default parameters to np.nan
                    assert param_value is init_param.default, failure_text
                else:
                    assert param_value == init_param.default, failure_text