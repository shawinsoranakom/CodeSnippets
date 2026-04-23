async def test_removing_disconnected_cams(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    config_entry: MockConfigEntry,
    reolink_host: MagicMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    attr: str | None,
    value: Any,
    expected_models: list[str],
) -> None:
    """Test device and entity registry are cleaned up when camera is removed."""
    reolink_host.channels = [0]
    assert await async_setup_component(hass, "config", {})
    client = await hass_ws_client(hass)
    # setup CH 0 and NVR switch entities/device
    with patch("homeassistant.components.reolink.PLATFORMS", [Platform.SWITCH]):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    device_models = [device.model for device in device_entries]
    assert sorted(device_models) == sorted([TEST_HOST_MODEL, TEST_CAM_MODEL])

    # Try to remove the device after 'disconnecting' a camera.
    if attr is not None:
        setattr(reolink_host, attr, value)
    expected_success = TEST_CAM_MODEL not in expected_models
    for device in device_entries:
        if device.model == TEST_CAM_MODEL:
            response = await client.remove_device(device.id, config_entry.entry_id)
            assert response["success"] == expected_success

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    device_models = [device.model for device in device_entries]
    assert sorted(device_models) == sorted(expected_models)