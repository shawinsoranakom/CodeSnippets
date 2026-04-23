def test_xfail_count_with_no_fast_fail():
    """Test that the right number of xfail warnings are raised when on_fail is "warn".

    It also checks the number of raised EstimatorCheckFailedWarning, and checks the
    output of check_estimator.
    """
    est = NuSVC()
    expected_failed_checks = _get_expected_failed_checks(est)
    # This is to make sure we test a class that has some expected failures
    assert len(expected_failed_checks) > 0
    with warnings.catch_warnings(record=True) as records:
        logs = check_estimator(
            est,
            expected_failed_checks=expected_failed_checks,
            on_fail="warn",
        )
    xfail_warns = [w for w in records if w.category != SkipTestWarning]
    assert all([rec.category == EstimatorCheckFailedWarning for rec in xfail_warns])
    assert len(xfail_warns) == len(expected_failed_checks)

    xfailed = [log for log in logs if log["status"] == "xfail"]
    assert len(xfailed) == len(expected_failed_checks)