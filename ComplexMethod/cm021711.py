async def test_significant_change(hass: HomeAssistant) -> None:
    """Detect update significant changes."""
    assert async_check_significant_change(hass, STATE_ON, {}, STATE_OFF, {})
    assert async_check_significant_change(hass, STATE_OFF, {}, STATE_ON, {})
    assert not async_check_significant_change(hass, STATE_OFF, {}, STATE_OFF, {})
    assert not async_check_significant_change(hass, STATE_ON, {}, STATE_ON, {})

    attrs = {
        ATTR_INSTALLED_VERSION: "1.0.0",
        ATTR_IN_PROGRESS: False,
        ATTR_LATEST_VERSION: "1.0.1",
        ATTR_RELEASE_SUMMARY: "Fixes!",
        ATTR_RELEASE_URL: "https://www.example.com",
        ATTR_SKIPPED_VERSION: None,
        ATTR_TITLE: "Piece of Software",
    }
    assert not async_check_significant_change(hass, STATE_ON, attrs, STATE_ON, attrs)

    assert async_check_significant_change(
        hass,
        STATE_ON,
        attrs,
        STATE_ON,
        attrs.copy() | {ATTR_INSTALLED_VERSION: "1.0.1"},
    )

    assert async_check_significant_change(
        hass,
        STATE_ON,
        attrs,
        STATE_ON,
        attrs.copy() | {ATTR_LATEST_VERSION: "1.0.2"},
    )

    assert not async_check_significant_change(
        hass,
        STATE_ON,
        attrs,
        STATE_ON,
        attrs.copy() | {ATTR_IN_PROGRESS: True},
    )

    assert not async_check_significant_change(
        hass,
        STATE_ON,
        attrs,
        STATE_ON,
        attrs.copy() | {ATTR_RELEASE_SUMMARY: "More fixes!"},
    )

    assert not async_check_significant_change(
        hass,
        STATE_ON,
        attrs,
        STATE_ON,
        attrs.copy() | {ATTR_RELEASE_URL: "https://www.example.com/changed_url"},
    )

    assert not async_check_significant_change(
        hass,
        STATE_ON,
        attrs,
        STATE_ON,
        attrs.copy() | {ATTR_SKIPPED_VERSION: "1.0.0"},
    )

    assert not async_check_significant_change(
        hass,
        STATE_ON,
        attrs,
        STATE_ON,
        attrs.copy() | {ATTR_TITLE: "Renamed the software..."},
    )