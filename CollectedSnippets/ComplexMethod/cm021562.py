async def test_binary_sensors_without_corona_filter(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry_default_filter: MockConfigEntry,
    mock_nina_class: AsyncMock,
    nina_warnings: list[Warning],
) -> None:
    """Test the creation and values of the NINA binary sensors without the corona filter."""

    await setup_single_platform(
        hass,
        mock_config_entry_default_filter,
        Platform.BINARY_SENSOR,
        mock_nina_class,
        nina_warnings,
    )

    state_w1 = hass.states.get("binary_sensor.aach_stadt_warning_1")

    assert state_w1.state == STATE_ON
    assert (
        state_w1.attributes.get(ATTR_HEADLINE)
        == "Corona-Verordnung des Landes: Warnstufe durch Landesgesundheitsamt ausgerufen"
    )

    state_w2 = hass.states.get("binary_sensor.aach_stadt_warning_2")

    assert state_w2.state == STATE_ON
    assert state_w2.attributes.get(ATTR_HEADLINE) == "Ausfall Notruf 112"

    state_w3 = hass.states.get("binary_sensor.aach_stadt_warning_3")

    assert state_w3.state == STATE_OFF  # Warning expired

    state_w4 = hass.states.get("binary_sensor.aach_stadt_warning_4")

    assert state_w4.state == STATE_OFF

    state_w5 = hass.states.get("binary_sensor.aach_stadt_warning_5")

    assert state_w5.state == STATE_OFF