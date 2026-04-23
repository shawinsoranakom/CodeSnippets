async def test_device_registry(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    port,
    entry_type,
) -> None:
    """Test device registry integration."""
    assert await async_setup_component(hass, "config", {})

    entity_id = "media_player.speaker"

    info = get_fake_chromecast_info(port=port)

    chromecast, _ = await async_setup_media_player_cast(hass, info)
    chromecast.cast_type = pychromecast.const.CAST_TYPE_CHROMECAST
    _, conn_status_cb, _ = get_status_callbacks(chromecast)
    cast_entry = hass.config_entries.async_entries("cast")[0]

    connection_status = MagicMock()
    connection_status.status = "CONNECTED"
    conn_status_cb(connection_status)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.name == "Speaker"
    assert state.state == "off"
    assert entity_id == entity_registry.async_get_entity_id(
        "media_player", "cast", str(info.uuid)
    )
    entity_entry = entity_registry.async_get(entity_id)
    device_entry = device_registry.async_get(entity_entry.device_id)
    assert entity_entry.device_id == device_entry.id
    assert device_entry.entry_type == entry_type

    # Check that the chromecast object is torn down when the device is removed
    chromecast.disconnect.assert_not_called()

    client = await hass_ws_client(hass)
    response = await client.remove_device(device_entry.id, cast_entry.entry_id)
    assert response["success"]

    await hass.async_block_till_done()
    await hass.async_block_till_done()
    chromecast.disconnect.assert_called_once()

    assert entity_registry.async_get(entity_id) is None
    assert device_registry.async_get(entity_entry.device_id) is None