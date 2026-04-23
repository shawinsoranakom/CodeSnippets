def _get_curve(start_y: int,
               end_y: int,
               num_points: int,
               scale: float,
               mode: T.Literal["full", "cap_max", "cap_min"] = "full") -> list[int]:
    """ Obtain a curve.

    For the given start and end y values, return the y co-ordinates of a curve for the given
    number of points. The points are rounded down to the nearest 8.

    Parameters
    ----------
    start_y: int
        The y co-ordinate for the starting point of the curve
    end_y: int
        The y co-ordinate for the end point of the curve
    num_points: int
        The number of data points to plot on the x-axis
    scale: float
        The scale of the curve (from -.99 to 0.99)
    slope_mode: str, optional
        The method to generate the curve. One of `"full"`, `"cap_max"` or `"cap_min"`. `"full"`
        mode generates a curve from the `"start_y"` to the `"end_y"` values. `"cap_max"` pads the
        earlier points with the `"start_y"` value before filling out the remaining points at a
        fixed divider to the `"end_y"` value. `"cap_min"` starts at the `"start_y" filling points
        at a fixed divider until the `"end_y"` value is reached and pads the remaining points with
        the `"end_y"` value. Default: `"full"`

    Returns
    -------
    list
        List of ints of points for the given curve
     """
    scale = min(.99, max(-.99, scale))
    logger.debug("Obtaining curve: (start_y: %s, end_y: %s, num_points: %s, scale: %s, mode: %s)",
                 start_y, end_y, num_points, scale, mode)
    if mode == "full":
        x_axis = np.linspace(0., 1., num=num_points)
        y_axis: np.ndarray | list[int] = (x_axis - x_axis * scale) / (scale - abs(x_axis)
                                                                      * 2 * scale + 1)
        y_axis = T.cast(np.ndarray, y_axis) * (end_y - start_y) + start_y
        retval = [int((y // 8) * 8) for y in y_axis]
    else:
        y_axis = [start_y]
        scale = 1. - abs(scale)
        for _ in range(num_points - 1):
            current_value = max(end_y, int(((y_axis[-1] * scale) // 8) * 8))
            y_axis.append(current_value)
            if current_value == end_y:
                break
        pad = [start_y if mode == "cap_max" else end_y for _ in range(num_points - len(y_axis))]
        retval = pad + y_axis if mode == "cap_max" else y_axis + pad
    logger.debug("Returning curve: %s", retval)
    return retval