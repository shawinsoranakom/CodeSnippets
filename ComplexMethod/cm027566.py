def parse_time_expression(parameter: Any, min_value: int, max_value: int) -> list[int]:
    """Parse the time expression part and return a list of times to match."""
    if parameter is None or parameter == "*":
        res = list(range(min_value, max_value + 1))
    elif isinstance(parameter, str):
        if parameter.startswith("/"):
            parameter = int(parameter[1:])
            res = list(
                range(min_value + (-min_value % parameter), max_value + 1, parameter)
            )
        else:
            res = [int(parameter)]

    elif not hasattr(parameter, "__iter__"):
        res = [int(parameter)]
    else:
        res = sorted(int(x) for x in parameter)

    for val in res:
        if val < min_value or val > max_value:
            raise ValueError(
                f"Time expression '{parameter}': parameter {val} out of range "
                f"({min_value} to {max_value})"
            )

    return res