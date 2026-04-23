async def test_shelly_2pm_gen3_no_relay_names(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    device_registry: DeviceRegistry,
    monkeypatch: pytest.MonkeyPatch,
    snapshot: SnapshotAssertion,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test Shelly 2PM Gen3 without relay names.

    This device has two relays/channels,we should get a main device and two sub
    devices.
    """
    device_fixture = await async_load_json_object_fixture(hass, "2pm_gen3.json", DOMAIN)
    monkeypatch.setattr(mock_rpc_device, "shelly", device_fixture["shelly"])
    monkeypatch.setattr(mock_rpc_device, "status", device_fixture["status"])
    monkeypatch.setattr(mock_rpc_device, "config", device_fixture["config"])

    await force_uptime_value(hass, freezer)

    config_entry = await init_integration(hass, gen=3, model=MODEL_2PM_G3)

    # Relay 0 sub-device
    entity_id = "switch.test_name_output_0"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Test name Output 0"

    entity_id = "sensor.test_name_output_0_power"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Test name Output 0"

    # Relay 1 sub-device
    entity_id = "switch.test_name_output_1"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Test name Output 1"

    entity_id = "sensor.test_name_output_1_power"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Test name Output 1"

    # Main device
    entity_id = "update.test_name_firmware"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Test name"

    await snapshot_device_entities(
        hass, entity_registry, snapshot, config_entry.entry_id
    )