def check_joint_types(parameters: dict[str, tuple[Any, Any]]) -> None:
    """Checks if all parameters have types that allow to execute a function.
    If parameters are {'a': (a, TimeEventType), 'b': (b, IntervalType)} then
    the following pairs of types are allowed for (a, b): (int, int), (float, float),
    (datetime.datetime, datetime.timedelta)
    """

    parameters = {
        name: (variable, expected_type)
        for name, (variable, expected_type) in parameters.items()
        if variable is not None
    }
    types = {name: eval_type(variable) for name, (variable, _) in parameters.items()}
    expected_types = []
    for i in range(len(_get_possible_types(TimeEventType))):
        expected_types.append(
            {
                name: _get_possible_types(expected_type)[i]
                for name, (_variable, expected_type) in parameters.items()
            }
        )
    for ex_types in expected_types:
        if all(
            [
                dt.dtype_issubclass(dtype, ex_dtype)
                for (dtype, ex_dtype) in zip(types.values(), ex_types.values())
            ]
        ):
            break
    else:
        expected_types_string = " or ".join(
            repr(tuple(ex_types.values())) for ex_types in expected_types
        )
        raise TypeError(
            f"Arguments ({', '.join(parameters.keys())}) have to be of types "
            + f"{expected_types_string} but are of types {tuple(types.values())}."
        )