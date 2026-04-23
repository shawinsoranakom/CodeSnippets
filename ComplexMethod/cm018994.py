async def test_update_enable_leds(
    hass: HomeAssistant,
    mock_device: MockDevice,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
) -> None:
    """Test state change of a enable_leds switch device."""
    entry = configure_integration(hass)
    device_name = entry.title.replace(" ", "_").lower()
    entity_id = f"{SWITCH_DOMAIN}.{device_name}_enable_leds"

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id) == snapshot
    assert entity_registry.async_get(entity_id) == snapshot

    # Emulate state change
    mock_device.device.async_get_led_setting.return_value = True
    freezer.tick(SHORT_UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON

    # Switch off
    mock_device.device.async_get_led_setting.return_value = False
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF
    mock_device.device.async_set_led_setting.assert_called_once_with(False)
    mock_device.device.async_set_led_setting.reset_mock()

    freezer.tick(REQUEST_REFRESH_DEFAULT_COOLDOWN)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Switch on
    mock_device.device.async_get_led_setting.return_value = True
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: entity_id}, blocking=True
    )

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    mock_device.device.async_set_led_setting.assert_called_once_with(True)
    mock_device.device.async_set_led_setting.reset_mock()

    freezer.tick(REQUEST_REFRESH_DEFAULT_COOLDOWN)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Device unavailable
    mock_device.device.async_get_led_setting.side_effect = DeviceUnavailable()
    mock_device.device.async_set_led_setting.side_effect = DeviceUnavailable()

    with pytest.raises(
        HomeAssistantError, match=f"Device {entry.title} did not respond"
    ):
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE