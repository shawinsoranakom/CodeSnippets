def _convert_skia_path_to_vmobject(
    path: pathops.Path,
    vmobject: VMobject
) -> VMobject:
    PathVerb = pathops.PathVerb
    current_path_start = np.array([0.0, 0.0, 0.0])
    for path_verb, points in path:
        if path_verb == PathVerb.CLOSE:
            vmobject.add_line_to(current_path_start)
        else:
            points = np.hstack((np.array(points), np.zeros((len(points), 1))))
            if path_verb == PathVerb.MOVE:
                for point in points:
                    current_path_start = point
                    vmobject.start_new_path(point)
            elif path_verb == PathVerb.CUBIC:
                vmobject.add_cubic_bezier_curve_to(*points)
            elif path_verb == PathVerb.LINE:
                vmobject.add_line_to(points[0])
            elif path_verb == PathVerb.QUAD:
                vmobject.add_quadratic_bezier_curve_to(*points)
            else:
                raise Exception(f"Unsupported: {path_verb}")
    return vmobject.reverse_points()