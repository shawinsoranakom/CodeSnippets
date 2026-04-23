def check_param_validation(name, estimator_orig):
    # Check that an informative error is raised when the value of a constructor
    # parameter does not have an appropriate type or value.
    rng = np.random.RandomState(0)
    X = rng.uniform(size=(20, 5))
    y = rng.randint(0, 2, size=20)
    y = _enforce_estimator_tags_y(estimator_orig, y)
    tags = get_tags(estimator_orig)

    estimator_params = estimator_orig.get_params(deep=False).keys()

    # check that there is a constraint for each parameter
    if estimator_params:
        validation_params = estimator_orig._parameter_constraints.keys()
        unexpected_params = set(validation_params) - set(estimator_params)
        missing_params = set(estimator_params) - set(validation_params)
        err_msg = (
            f"Mismatch between _parameter_constraints and the parameters of {name}."
            f"\nConsider the unexpected parameters {unexpected_params} and expected but"
            f" missing parameters {missing_params}"
        )
        assert validation_params == estimator_params, err_msg

    # this object does not have a valid type for sure for all params
    param_with_bad_type = type("BadType", (), {})()

    fit_methods = ["fit", "partial_fit", "fit_transform", "fit_predict"]

    for param_name in estimator_params:
        constraints = estimator_orig._parameter_constraints[param_name]

        if constraints == "no_validation":
            # This parameter is not validated
            continue

        # Mixing an interval of reals and an interval of integers must be avoided.
        if any(
            isinstance(constraint, Interval) and constraint.type == Integral
            for constraint in constraints
        ) and any(
            isinstance(constraint, Interval) and constraint.type == Real
            for constraint in constraints
        ):
            raise ValueError(
                f"The constraint for parameter {param_name} of {name} can't have a mix"
                " of intervals of Integral and Real types. Use the type RealNotInt"
                " instead of Real."
            )

        match = rf"The '{param_name}' parameter of {name} must be .* Got .* instead."
        err_msg = (
            f"{name} does not raise an informative error message when the "
            f"parameter {param_name} does not have a valid type or value."
        )

        estimator = clone(estimator_orig)

        # First, check that the error is raised if param doesn't match any valid type.
        estimator.set_params(**{param_name: param_with_bad_type})

        for method in fit_methods:
            if not hasattr(estimator, method):
                # the method is not accessible with the current set of parameters
                continue

            err_msg = (
                f"{name} does not raise an informative error message when the parameter"
                f" {param_name} does not have a valid type. If any Python type is"
                " valid, the constraint should be 'no_validation'."
            )

            with raises(InvalidParameterError, match=match, err_msg=err_msg):
                if tags.target_tags.one_d_labels or tags.target_tags.two_d_labels:
                    # The estimator is a label transformer and take only `y`
                    getattr(estimator, method)(y)
                else:
                    getattr(estimator, method)(X, y)

        # Then, for constraints that are more than a type constraint, check that the
        # error is raised if param does match a valid type but does not match any valid
        # value for this type.
        constraints = [make_constraint(constraint) for constraint in constraints]

        for constraint in constraints:
            try:
                bad_value = generate_invalid_param_val(constraint)
            except NotImplementedError:
                continue

            estimator.set_params(**{param_name: bad_value})

            for method in fit_methods:
                if not hasattr(estimator, method):
                    # the method is not accessible with the current set of parameters
                    continue

                err_msg = (
                    f"{name} does not raise an informative error message when the "
                    f"parameter {param_name} does not have a valid value.\n"
                    "Constraints should be disjoint. For instance "
                    "[StrOptions({'a_string'}), str] is not an acceptable set of "
                    "constraint because generating an invalid string for the first "
                    "constraint will always produce a valid string for the second "
                    "constraint."
                )

                with raises(InvalidParameterError, match=match, err_msg=err_msg):
                    if tags.target_tags.one_d_labels or tags.target_tags.two_d_labels:
                        # The estimator is a label transformer and take only `y`
                        getattr(estimator, method)(y)
                    else:
                        getattr(estimator, method)(X, y)