async def test_shelly_pro_3em_with_emeter_name(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    device_registry: DeviceRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test Shelly Pro 3EM when the name for Emeter is set.

    We should get the main device and three subdevices, one subdevice per one phase.
    """
    device_fixture = await async_load_json_object_fixture(hass, "pro_3em.json", DOMAIN)
    device_fixture["config"]["em:0"]["name"] = "Emeter name"
    monkeypatch.setattr(mock_rpc_device, "shelly", device_fixture["shelly"])
    monkeypatch.setattr(mock_rpc_device, "status", device_fixture["status"])
    monkeypatch.setattr(mock_rpc_device, "config", device_fixture["config"])

    await init_integration(hass, gen=2, model=MODEL_PRO_EM3)

    # Main device
    entity_id = "sensor.test_name_power"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Test name"

    # Phase A sub-device
    entity_id = "sensor.test_name_phase_a_power"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Test name Phase A"

    # Phase B sub-device
    entity_id = "sensor.test_name_phase_b_power"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Test name Phase B"

    # Phase C sub-device
    entity_id = "sensor.test_name_phase_c_power"

    state = hass.states.get(entity_id)
    assert state

    entry = entity_registry.async_get(entity_id)
    assert entry

    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry
    assert device_entry.name == "Test name Phase C"