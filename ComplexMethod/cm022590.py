async def test_dynamic_device_discovery(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_liebherr_client: MagicMock,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test new devices are automatically discovered on all platforms."""
    mock_config_entry.add_to_hass(hass)

    all_platforms = [
        Platform.SENSOR,
        Platform.NUMBER,
        Platform.SWITCH,
        Platform.SELECT,
    ]
    with patch(f"homeassistant.components.{DOMAIN}.PLATFORMS", all_platforms):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Initially only the original device exists
    assert hass.states.get("sensor.test_fridge_top_zone") is not None
    assert hass.states.get("sensor.new_fridge") is None

    # Simulate a new device appearing on the account
    mock_liebherr_client.get_devices.return_value = [MOCK_DEVICE, NEW_DEVICE]
    mock_liebherr_client.get_device_state.side_effect = lambda device_id, **kw: (
        copy.deepcopy(
            NEW_DEVICE_STATE if device_id == "new_device_id" else MOCK_DEVICE_STATE
        )
    )

    # Advance time to trigger device scan (5 minute interval)
    freezer.tick(timedelta(minutes=5, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # New device should have entities on all platforms
    state = hass.states.get("sensor.new_fridge")
    assert state is not None
    assert state.state == "4"
    assert hass.states.get("number.new_fridge_setpoint") is not None
    assert hass.states.get("switch.new_fridge_supercool") is not None
    assert hass.states.get("select.new_fridge_icemaker") is not None

    # Original device should still exist
    assert hass.states.get("sensor.test_fridge_top_zone") is not None

    # Both devices should be in the device registry
    assert device_registry.async_get_device(identifiers={(DOMAIN, "new_device_id")})
    assert device_registry.async_get_device(identifiers={(DOMAIN, "test_device_id")})