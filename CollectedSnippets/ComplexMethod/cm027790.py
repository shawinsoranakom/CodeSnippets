def smooth_quadratic_path(anchors: Vect3Array) -> Vect3Array:
    """
    Returns a path defining a smooth quadratic bezier spline
    through anchors.
    """
    if len(anchors) < 2:
        return anchors
    elif len(anchors) == 2:
        return np.array([anchors[0], anchors.mean(0), anchors[1]])

    is_flat = (anchors[:, 2] == 0).all()
    if not is_flat:
        normal = cross(anchors[2] - anchors[1], anchors[1] - anchors[0])
        rot = z_to_vector(normal)
        anchors = np.dot(anchors, rot)
        shift = anchors[0, 2]
        anchors[:, 2] -= shift
    h1s, h2s = get_smooth_cubic_bezier_handle_points(anchors)
    quads = [anchors[0, :2]]
    for cub_bs in zip(anchors[:-1], h1s, h2s, anchors[1:]):
        # Try to use fontTools curve_to_quadratic
        new_quads = curve_to_quadratic(
            [b[:2] for b in cub_bs],
            max_err=0.1 * get_norm(cub_bs[3] - cub_bs[0])
        )
        # Otherwise fall back on home baked solution
        if new_quads is None or len(new_quads) % 2 == 0:
            new_quads = get_quadratic_approximation_of_cubic(*cub_bs)[:, :2]
        quads.extend(new_quads[1:])
    new_path = np.zeros((len(quads), 3))
    new_path[:, :2] = quads
    if not is_flat:
        new_path[:, 2] += shift
        new_path = np.dot(new_path, rot.T)
    return new_path