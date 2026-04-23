async def test_stale_device_removal(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_liebherr_client: MagicMock,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test stale devices are removed when no longer returned by the API."""
    mock_config_entry.add_to_hass(hass)

    all_platforms = [
        Platform.SENSOR,
        Platform.NUMBER,
        Platform.SWITCH,
        Platform.SELECT,
    ]

    # Start with two devices
    mock_liebherr_client.get_devices.return_value = [MOCK_DEVICE, NEW_DEVICE]
    mock_liebherr_client.get_device_state.side_effect = lambda device_id, **kw: (
        copy.deepcopy(
            NEW_DEVICE_STATE if device_id == "new_device_id" else MOCK_DEVICE_STATE
        )
    )

    with patch(f"homeassistant.components.{DOMAIN}.PLATFORMS", all_platforms):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # Both devices should exist
    assert device_registry.async_get_device(identifiers={(DOMAIN, "test_device_id")})
    assert device_registry.async_get_device(identifiers={(DOMAIN, "new_device_id")})
    assert hass.states.get("sensor.test_fridge_top_zone") is not None
    assert hass.states.get("sensor.new_fridge") is not None

    # Verify both devices are in the device registry
    assert device_registry.async_get_device(identifiers={(DOMAIN, "test_device_id")})
    new_device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, "new_device_id")}
    )
    assert new_device_entry

    # Simulate the new device being removed from the account.
    # Make get_device_state raise for new_device_id so we can detect
    # if the stale coordinator is still polling after shutdown.
    mock_liebherr_client.get_devices.return_value = [MOCK_DEVICE]

    def _get_device_state_after_removal(device_id: str, **kw: Any) -> DeviceState:
        if device_id == "new_device_id":
            raise AssertionError(
                "get_device_state called for removed device new_device_id"
            )
        return copy.deepcopy(MOCK_DEVICE_STATE)

    mock_liebherr_client.get_device_state.side_effect = _get_device_state_after_removal

    freezer.tick(timedelta(minutes=5, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Stale device should be removed from device registry
    assert device_registry.async_get_device(identifiers={(DOMAIN, "test_device_id")})
    assert not device_registry.async_get_device(identifiers={(DOMAIN, "new_device_id")})

    # Advance past the coordinator update interval to confirm the stale
    # coordinator is no longer polling (would raise AssertionError above)
    freezer.tick(timedelta(seconds=61))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Original device should still work
    assert hass.states.get("sensor.test_fridge_top_zone") is not None
    assert mock_config_entry.state is ConfigEntryState.LOADED