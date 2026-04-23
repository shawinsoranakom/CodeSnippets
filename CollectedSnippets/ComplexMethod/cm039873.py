def validate_parameter_constraints(parameter_constraints, params, caller_name):
    """Validate types and values of given parameters.

    Parameters
    ----------
    parameter_constraints : dict or {"no_validation"}
        If "no_validation", validation is skipped for this parameter.

        If a dict, it must be a dictionary `param_name: list of constraints`.
        A parameter is valid if it satisfies one of the constraints from the list.
        Constraints can be:
        - an Interval object, representing a continuous or discrete range of numbers
        - the string "array-like"
        - the string "sparse matrix"
        - the string "random_state"
        - callable
        - None, meaning that None is a valid value for the parameter
        - any type, meaning that any instance of this type is valid
        - an Options object, representing a set of elements of a given type
        - a StrOptions object, representing a set of strings
        - the string "boolean"
        - the string "verbose"
        - the string "cv_object"
        - the string "nan"
        - a MissingValues object representing markers for missing values
        - a HasMethods object, representing method(s) an object must have
        - a Hidden object, representing a constraint not meant to be exposed to the user

    params : dict
        A dictionary `param_name: param_value`. The parameters to validate against the
        constraints.

    caller_name : str
        The name of the estimator or function or method that called this function.
    """
    for param_name, param_val in params.items():
        # We allow parameters to not have a constraint so that third party estimators
        # can inherit from sklearn estimators without having to necessarily use the
        # validation tools.
        if param_name not in parameter_constraints:
            continue

        constraints = parameter_constraints[param_name]

        if constraints == "no_validation":
            continue

        constraints = [make_constraint(constraint) for constraint in constraints]

        for constraint in constraints:
            if constraint.is_satisfied_by(param_val):
                # this constraint is satisfied, no need to check further.
                break
        else:
            # No constraint is satisfied, raise with an informative message.

            # Ignore constraints that we don't want to expose in the error message,
            # i.e. options that are for internal purpose or not officially supported.
            constraints = [
                constraint for constraint in constraints if not constraint.hidden
            ]

            if len(constraints) == 1:
                constraints_str = f"{constraints[0]}"
            else:
                constraints_str = (
                    f"{', '.join([str(c) for c in constraints[:-1]])} or"
                    f" {constraints[-1]}"
                )

            raise InvalidParameterError(
                f"The {param_name!r} parameter of {caller_name} must be"
                f" {constraints_str}. Got {param_val!r} instead."
            )