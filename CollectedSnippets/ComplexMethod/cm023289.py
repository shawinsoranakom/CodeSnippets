async def test_update_entity_states(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    climate_radio_thermostat_ct100_plus_different_endpoints: Node,
    integration: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
    hass_ws_client: WebSocketGenerator,
    entity_id: str,
    installed_version: str,
) -> None:
    """Test update entity states."""
    ws_client = await hass_ws_client(hass)

    assert client.driver.controller.sdk_version == "6.50.0"

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    client.async_send_command.return_value = {"updates": []}

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15, days=1))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    await ws_client.send_json(
        {
            "id": 1,
            "type": "update/release_notes",
            "entity_id": entity_id,
        }
    )
    result = await ws_client.receive_json()
    assert result["result"] is None

    client.async_send_command.return_value = FIRMWARE_UPDATES

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15, days=2))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    attrs = state.attributes
    assert not attrs[ATTR_AUTO_UPDATE]
    assert attrs[ATTR_INSTALLED_VERSION] == installed_version
    assert attrs[ATTR_IN_PROGRESS] is False
    assert attrs[ATTR_LATEST_VERSION] == "11.2.4"
    assert attrs[ATTR_RELEASE_URL] is None
    assert attrs[ATTR_UPDATE_PERCENTAGE] is None

    await ws_client.send_json(
        {
            "id": 2,
            "type": "update/release_notes",
            "entity_id": entity_id,
        }
    )
    result = await ws_client.receive_json()
    assert result["result"] == "blah 2"

    # Refresh value should not be supported by this entity
    await hass.services.async_call(
        DOMAIN,
        SERVICE_REFRESH_VALUE,
        {
            ATTR_ENTITY_ID: entity_id,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert "There is no value to refresh for this entity" in caplog.text

    client.async_send_command.return_value = {"updates": []}

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15, days=3))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF