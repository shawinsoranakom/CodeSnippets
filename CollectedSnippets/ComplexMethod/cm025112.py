def test_iif(hass: HomeAssistant) -> None:
    """Test the immediate if function/filter."""

    result = render(hass, "{{ (1 == 1) | iif }}")
    assert result is True

    result = render(hass, "{{ (1 == 2) | iif }}")
    assert result is False

    result = render(hass, "{{ (1 == 1) | iif('yes') }}")
    assert result == "yes"

    result = render(hass, "{{ (1 == 2) | iif('yes') }}")
    assert result is False

    result = render(hass, "{{ (1 == 2) | iif('yes', 'no') }}")
    assert result == "no"

    result = render(hass, "{{ not_exists | default(None) | iif('yes', 'no') }}")
    assert result == "no"

    result = render(
        hass, "{{ not_exists | default(None) | iif('yes', 'no', 'unknown') }}"
    )
    assert result == "unknown"

    result = render(hass, "{{ iif(1 == 1) }}")
    assert result is True

    result = render(hass, "{{ iif(1 == 2, 'yes', 'no') }}")
    assert result == "no"