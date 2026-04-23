async def test_update_plc_phyrates(
    hass: HomeAssistant,
    mock_device: MockDevice,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
    snapshot: SnapshotAssertion,
) -> None:
    """Test state change of plc_downlink_phyrate and plc_uplink_phyrate sensor devices."""
    entry = configure_integration(hass)
    device_name = entry.title.replace(" ", "_").lower()
    entity_id_downlink = f"{SENSOR_DOMAIN}.{device_name}_plc_downlink_phy_rate_{PLCNET.devices[1].user_device_name}"
    entity_id_uplink = f"{SENSOR_DOMAIN}.{device_name}_plc_uplink_phy_rate_{PLCNET.devices[1].user_device_name}"
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id_downlink) == snapshot
    assert entity_registry.async_get(entity_id_downlink) == snapshot
    assert hass.states.get(entity_id_downlink) == snapshot
    assert entity_registry.async_get(entity_id_downlink) == snapshot

    # Emulate device failure
    mock_device.plcnet.async_get_network_overview = AsyncMock(
        side_effect=DeviceUnavailable
    )
    freezer.tick(LONG_UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id_downlink)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    state = hass.states.get(entity_id_uplink)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Emulate state change
    mock_device.reset()
    freezer.tick(LONG_UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id_downlink)
    assert state is not None
    assert state.state == str(PLCNET.data_rates[0].rx_rate)

    state = hass.states.get(entity_id_uplink)
    assert state is not None
    assert state.state == str(PLCNET.data_rates[0].tx_rate)