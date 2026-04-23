def _compare_run_with_error(run: Any, expected_run: Any) -> None:
    if run.child_runs:
        assert len(expected_run.child_runs) == len(run.child_runs)
        for received, expected in zip(
            run.child_runs, expected_run.child_runs, strict=False
        ):
            _compare_run_with_error(received, expected)
    received = pydantic_to_dict(run, exclude={"child_runs"})
    received_err = received.pop("error")
    expected = pydantic_to_dict(expected_run, exclude={"child_runs"})
    expected_err = expected.pop("error")

    assert received == expected
    if expected_err is not None:
        assert received_err is not None
        assert expected_err in received_err
    else:
        assert received_err is None