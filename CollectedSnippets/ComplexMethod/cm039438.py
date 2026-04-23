def assert_children_values_monotonic(predictor, monotonic_cst):
    # Make sure siblings values respect the monotonic constraints. Left should
    # be lower (resp greater) than right child if constraint is POS (resp.
    # NEG).
    # Note that this property alone isn't enough to ensure full monotonicity,
    # since we also need to guanrantee that all the descendents of the left
    # child won't be greater (resp. lower) than the right child, or its
    # descendents. That's why we need to bound the predicted values (this is
    # tested in assert_children_values_bounded)
    nodes = predictor.nodes
    left_lower = []
    left_greater = []
    for node in nodes:
        if node["is_leaf"]:
            continue

        left_idx = node["left"]
        right_idx = node["right"]

        if nodes[left_idx]["value"] < nodes[right_idx]["value"]:
            left_lower.append(node)
        elif nodes[left_idx]["value"] > nodes[right_idx]["value"]:
            left_greater.append(node)

    if monotonic_cst == MonotonicConstraint.NO_CST:
        assert left_lower and left_greater
    elif monotonic_cst == MonotonicConstraint.POS:
        assert left_lower and not left_greater
    else:  # NEG
        assert not left_lower and left_greater