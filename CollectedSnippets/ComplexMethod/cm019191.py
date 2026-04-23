async def test_removing_chime(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    config_entry: MockConfigEntry,
    reolink_host: MagicMock,
    reolink_chime: MagicMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    attr: str | None,
    value: Any,
    expected_models: list[str],
    expected_remove_call_count: int,
) -> None:
    """Test removing a chime."""
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
    assert sorted(device_models) == sorted(
        [TEST_HOST_MODEL, TEST_CAM_MODEL, CHIME_MODEL]
    )

    if attr == "remove":

        async def test_remove_chime(*args, **key_args):
            """Remove chime."""
            reolink_chime.connect_state = -1

        reolink_chime.remove = AsyncMock(side_effect=test_remove_chime)
    elif attr is not None:
        setattr(reolink_chime, attr, value)

    # Try to remove the device after 'disconnecting' a chime.
    expected_success = CHIME_MODEL not in expected_models
    for device in device_entries:
        if device.model == CHIME_MODEL:
            response = await client.remove_device(device.id, config_entry.entry_id)
            assert response["success"] == expected_success
            assert reolink_chime.remove.call_count == expected_remove_call_count

    device_entries = dr.async_entries_for_config_entry(
        device_registry, config_entry.entry_id
    )
    device_models = [device.model for device in device_entries]
    assert sorted(device_models) == sorted(expected_models)