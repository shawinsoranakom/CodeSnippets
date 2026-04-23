async def test_automatic_device_addition_and_removal(
    hass: HomeAssistant,
    load_int: ConfigEntry,
    mock_client: MagicMock,
    get_data: tuple[SensiboData, dict[str, Any], dict[str, Any]],
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
    entity_id: str,
    device_ids: list[str],
) -> None:
    """Test for automatic device addition and removal."""

    state = hass.states.get(entity_id)
    assert state
    assert entity_registry.async_get(entity_id)
    for device_id in device_ids:
        assert device_registry.async_get_device(identifiers={(DOMAIN, device_id)})

    # Remove one of the devices
    new_device_list = [
        device for device in get_data[2]["result"] if device["id"] != device_ids[0]
    ]
    mock_client.async_get_devices.return_value = {
        "status": "success",
        "result": new_device_list,
    }
    new_data = {k: v for k, v in get_data[0].parsed.items() if k != device_ids[0]}
    new_raw = mock_client.async_get_devices.return_value["result"]
    mock_client.async_get_devices_data.return_value = SensiboData(new_raw, new_data)

    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert not state
    assert not entity_registry.async_get(entity_id)
    for device_id in device_ids:
        assert not device_registry.async_get_device(identifiers={(DOMAIN, device_id)})

    # Add the device back
    mock_client.async_get_devices.return_value = get_data[2]
    mock_client.async_get_devices_data.return_value = get_data[0]

    freezer.tick(timedelta(minutes=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert entity_registry.async_get(entity_id)
    for device_id in device_ids:
        assert device_registry.async_get_device(identifiers={(DOMAIN, device_id)})