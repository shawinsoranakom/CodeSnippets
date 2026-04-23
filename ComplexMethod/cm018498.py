async def test_rpc_sleeping_update_entity_service(
    hass: HomeAssistant,
    mock_rpc_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test RPC sleeping device when the update_entity service is used."""
    await async_setup_component(hass, "homeassistant", {})

    entity_id = f"{SENSOR_DOMAIN}.test_name_temperature"
    monkeypatch.setattr(mock_rpc_device, "connected", False)
    monkeypatch.setitem(mock_rpc_device.status["sys"], "wakeup_period", 1000)
    await init_integration(hass, 2, sleep_period=1000)

    # Make device online
    mock_rpc_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (state := hass.states.get(entity_id))
    assert state.state == "22.9"

    await hass.services.async_call(
        HA_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        service_data={ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Entity should be available after update_entity service call
    assert (state := hass.states.get(entity_id))
    assert state.state == "22.9"

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-temperature:0-temperature_tc"

    assert (
        "Entity sensor.test_name_temperature comes from a sleeping device"
        in caplog.text
    )