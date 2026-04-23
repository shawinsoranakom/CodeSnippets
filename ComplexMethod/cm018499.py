async def test_block_sleeping_update_entity_service(
    hass: HomeAssistant,
    mock_block_device: Mock,
    entity_registry: EntityRegistry,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test block sleeping device when the update_entity service is used."""
    await async_setup_component(hass, "homeassistant", {})

    entity_id = f"{SENSOR_DOMAIN}.test_name_temperature"
    monkeypatch.setitem(
        mock_block_device.settings,
        "sleep_mode",
        {"period": 60, "unit": "m"},
    )
    await init_integration(hass, 1, sleep_period=3600)

    # Sensor should be created when device is online
    assert hass.states.get(entity_id) is None

    # Make device online
    mock_block_device.mock_online()
    await hass.async_block_till_done(wait_background_tasks=True)

    assert (state := hass.states.get(entity_id))
    assert state.state == "22.1"

    await hass.services.async_call(
        HA_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        service_data={ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    # Entity should be available after update_entity service call
    assert (state := hass.states.get(entity_id))
    assert state.state == "22.1"

    assert (entry := entity_registry.async_get(entity_id))
    assert entry.unique_id == "123456789ABC-sensor_0-temp"

    assert (
        "Entity sensor.test_name_temperature comes from a sleeping device"
        in caplog.text
    )