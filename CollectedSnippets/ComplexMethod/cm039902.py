def check_outlier_contamination(name, estimator_orig):
    # Check that the contamination parameter is in (0.0, 0.5] when it is an
    # interval constraint.

    if not hasattr(estimator_orig, "_parameter_constraints"):
        # Only estimator implementing parameter constraints will be checked
        return

    if "contamination" not in estimator_orig._parameter_constraints:
        return

    contamination_constraints = estimator_orig._parameter_constraints["contamination"]
    if not any([isinstance(c, Interval) for c in contamination_constraints]):
        raise AssertionError(
            "contamination constraints should contain a Real Interval constraint."
        )

    for constraint in contamination_constraints:
        if isinstance(constraint, Interval):
            assert (
                constraint.type == Real
                and constraint.left >= 0.0
                and constraint.right <= 0.5
                and (constraint.left > 0 or constraint.closed in {"right", "neither"})
            ), "contamination constraint should be an interval in (0, 0.5]"