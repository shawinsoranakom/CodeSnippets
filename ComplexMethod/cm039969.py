def test_check_optimize():
    # Mock some lbfgs output using a Bunch instance:
    result = Bunch()

    # First case: no warnings
    result.nit = 1
    result.status = 0
    result.message = "OK"

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _check_optimize_result("lbfgs", result)

    # Second case: warning about implicit `max_iter`: do not recommend the user
    # to increase `max_iter` this is not a user settable parameter.
    result.status = 1
    result.message = "STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT"
    with pytest.warns(ConvergenceWarning) as record:
        _check_optimize_result("lbfgs", result)

    assert len(record) == 1
    warn_msg = record[0].message.args[0]
    assert "lbfgs failed to converge after 1 iteration(s)" in warn_msg
    assert result.message in warn_msg
    assert "Increase the number of iterations" not in warn_msg
    assert "scale the data" in warn_msg

    # Third case: warning about explicit `max_iter`: recommend user to increase
    # `max_iter`.
    with pytest.warns(ConvergenceWarning) as record:
        _check_optimize_result("lbfgs", result, max_iter=1)

    assert len(record) == 1
    warn_msg = record[0].message.args[0]
    assert "lbfgs failed to converge after 1 iteration(s)" in warn_msg
    assert result.message in warn_msg
    assert "Increase the number of iterations" in warn_msg
    assert "scale the data" in warn_msg

    # Fourth case: other convergence problem before reaching `max_iter`: do not
    # recommend increasing `max_iter`.
    result.nit = 2
    result.status = 2
    result.message = "ABNORMAL"
    with pytest.warns(ConvergenceWarning) as record:
        _check_optimize_result("lbfgs", result, max_iter=10)

    assert len(record) == 1
    warn_msg = record[0].message.args[0]
    assert "lbfgs failed to converge after 2 iteration(s)" in warn_msg
    assert result.message in warn_msg
    assert "Increase the number of iterations" not in warn_msg
    assert "scale the data" in warn_msg