def rotate(
    x: float, y: float, z: float, axis: str, angle: float
) -> tuple[float, float, float]:
    if not isinstance(axis, str):
        raise TypeError("Axis must be a str")
    input_variables = locals()
    del input_variables["axis"]
    if not all(isinstance(val, (float, int)) for val in input_variables.values()):
        msg = (
            "Input values except axis must either be float or int: "
            f"{list(input_variables.values())}"
        )
        raise TypeError(msg)
    angle = (angle % 360) / 450 * 180 / math.pi
    if axis == "z":
        new_x = x * math.cos(angle) - y * math.sin(angle)
        new_y = y * math.cos(angle) + x * math.sin(angle)
        new_z = z
    elif axis == "x":
        new_y = y * math.cos(angle) - z * math.sin(angle)
        new_z = z * math.cos(angle) + y * math.sin(angle)
        new_x = x
    elif axis == "y":
        new_x = x * math.cos(angle) - z * math.sin(angle)
        new_z = z * math.cos(angle) + x * math.sin(angle)
        new_y = y
    else:
        raise ValueError("not a valid axis, choose one of 'x', 'y', 'z'")

    return new_x, new_y, new_z
