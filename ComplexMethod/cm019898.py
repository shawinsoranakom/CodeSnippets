async def test_event_with_platform_context(hass: HomeAssistant) -> None:
    """Test extraction of platform context information during Sentry events."""

    current_platform_mock = Mock()
    current_platform_mock.get().platform_name = "hue"
    current_platform_mock.get().domain = "light"

    with patch(
        "homeassistant.components.sentry.entity_platform.current_platform",
        new=current_platform_mock,
    ):
        result = process_before_send(
            hass,
            options={},
            channel="test",
            huuid="12345",
            system_info={"installation_type": "pytest"},
            custom_components=["ironing_robot"],
            event={},
            hint={},
        )

    assert result
    assert result["tags"]["integration"] == "hue"
    assert result["tags"]["platform"] == "light"
    assert result["tags"]["custom_component"] == "no"

    current_platform_mock.get().platform_name = "ironing_robot"
    current_platform_mock.get().domain = "switch"

    with patch(
        "homeassistant.components.sentry.entity_platform.current_platform",
        new=current_platform_mock,
    ):
        result = process_before_send(
            hass,
            options={CONF_EVENT_CUSTOM_COMPONENTS: True},
            channel="test",
            huuid="12345",
            system_info={"installation_type": "pytest"},
            custom_components=["ironing_robot"],
            event={},
            hint={},
        )

    assert result
    assert result["tags"]["integration"] == "ironing_robot"
    assert result["tags"]["platform"] == "switch"
    assert result["tags"]["custom_component"] == "yes"