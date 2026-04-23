async def test_shelly_fk_06x_with_zone_names(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    device_registry: DeviceRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Shelly Irrigation controller FK-06X with zone names.

    We should get the main device and 6 subdevices, one subdevice per one zone.
    """
    device_fixture = await async_load_json_object_fixture(
        hass, "fk-06x_gen3_irrigation.json", DOMAIN
    )
    monkeypatch.setattr(mock_rpc_device, "shelly", device_fixture["shelly"])
    monkeypatch.setattr(mock_rpc_device, "status", device_fixture["status"])
    monkeypatch.setattr(mock_rpc_device, "config", device_fixture["config"])

    await init_integration(hass, gen=3, model=MODEL_FRANKEVER_IRRIGATION_CONTROLLER)

    # Main device
    entity_id = "sensor.test_name_average_temperature"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Test name"

    # 3 zones with names, 3 with default names
    zone_names = [
        "Zone Name 1",
        "Zone Name 2",
        "Zone Name 3",
        "Zone 4",
        "Zone 5",
        "Zone 6",
    ]

    for zone_name in zone_names:
        entity_id = f"valve.{zone_name.lower().replace(' ', '_')}"

        state = hass.states.get(entity_id)
        assert state

        entry = entity_registry.async_get(entity_id)
        assert entry

        device_entry = device_registry.async_get(entry.device_id)
        assert device_entry
        assert device_entry.name == zone_name