def test_estimator_checks_generator_strict_xfail_tests():
    # Make sure that the checks generator marks tests that are expected to fail
    # as strict xfail
    est = next(_construct_instances(NuSVC))
    expected_to_fail = _get_expected_failed_checks(est)
    checks = estimator_checks_generator(
        est,
        legacy=True,
        expected_failed_checks=expected_to_fail,
        mark="xfail",
        xfail_strict=True,
    )
    # make sure we use a class that has expected failures
    assert len(expected_to_fail) > 0
    strict_xfailed_checks = []

    # xfail'ed checks are wrapped in a ParameterSet, so below we extract
    # the things we need via a bit of a crutch: len()
    marked_checks = [c for c in checks if hasattr(c, "marks")]
    # make sure we use a class that has expected failures
    assert len(expected_to_fail) > 0

    for parameter_set in marked_checks:
        _, check = parameter_set.values
        first_mark = parameter_set.marks[0]
        if first_mark.kwargs["strict"]:
            strict_xfailed_checks.append(_check_name(check))

    # all checks expected to fail are marked as strict xfail
    assert set(expected_to_fail.keys()) == set(strict_xfailed_checks)