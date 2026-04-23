def test_deprecated_hass_argument(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    positional_arguments: list[str],
    keyword_arguments: dict[str, str],
    breaks_in_ha_version: str | None,
    extra_msg: str,
) -> None:
    """Test deprecated_hass_argument decorator."""

    calls = []

    @deprecated_hass_argument(breaks_in_ha_version=breaks_in_ha_version)
    def mock_deprecated_function(*args: str, **kwargs: str) -> None:
        calls.append((args, kwargs))

    mock_deprecated_function(*positional_arguments, **keyword_arguments)
    assert (
        "The deprecated argument hass was passed to mock_deprecated_function."
        f"{extra_msg}"
        " Use mock_deprecated_function without hass argument instead"
    ) not in caplog.text
    assert len(calls) == 1

    mock_deprecated_function(hass, *positional_arguments, **keyword_arguments)
    assert (
        "The deprecated argument hass was passed to mock_deprecated_function."
        f"{extra_msg}"
        " Use mock_deprecated_function without hass argument instead"
    ) in caplog.text
    assert len(calls) == 2

    caplog.clear()
    mock_deprecated_function(*positional_arguments, hass=hass, **keyword_arguments)
    assert (
        "The deprecated argument hass was passed to mock_deprecated_function."
        f"{extra_msg}"
        " Use mock_deprecated_function without hass argument instead"
    ) in caplog.text
    assert len(calls) == 3

    # Ensure that the two calls are the same, as the second call should have been
    # modified to remove the hass argument.
    assert calls[0] == calls[1]
    assert calls[0] == calls[2]