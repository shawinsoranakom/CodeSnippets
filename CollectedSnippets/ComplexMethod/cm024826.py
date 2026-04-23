def _assert_warnings_errors(
    res: HomeAssistantConfig,
    expected_warnings: list[CheckConfigError],
    expected_errors: list[CheckConfigError],
) -> None:
    assert len(res.warnings) == len(expected_warnings)
    assert len(res.errors) == len(expected_errors)

    expected_warning_str = ""
    expected_error_str = ""

    for idx, expected_warning in enumerate(expected_warnings):
        assert res.warnings[idx] == expected_warning
        expected_warning_str += expected_warning.message
    assert res.warning_str == expected_warning_str

    for idx, expected_error in enumerate(expected_errors):
        assert res.errors[idx] == expected_error
        expected_error_str += expected_error.message
    assert res.error_str == expected_error_str