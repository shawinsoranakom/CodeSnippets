async def test_poe_port_switches(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    aioclient_mock: AiohttpClientMocker,
    config_entry_setup: MockConfigEntry,
    mock_websocket_message: WebsocketMessageMock,
    device_payload: list[dict[str, Any]],
) -> None:
    """Test PoE port entities work."""
    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 0

    ent_reg_entry = entity_registry.async_get("switch.mock_name_port_1_poe")
    assert ent_reg_entry.disabled_by == RegistryEntryDisabler.INTEGRATION

    # Enable entity
    entity_registry.async_update_entity(
        entity_id="switch.mock_name_port_1_poe", disabled_by=None
    )
    entity_registry.async_update_entity(
        entity_id="switch.mock_name_port_2_poe", disabled_by=None
    )

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
    )
    await hass.async_block_till_done()

    # Validate state object
    assert hass.states.get("switch.mock_name_port_1_poe").state == STATE_ON

    # Update state object
    device_1 = deepcopy(device_payload[0])
    device_1["port_table"][0]["poe_mode"] = "off"
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)
    await hass.async_block_till_done()
    assert hass.states.get("switch.mock_name_port_1_poe").state == STATE_OFF

    # Turn off PoE
    aioclient_mock.clear_requests()
    aioclient_mock.put(
        f"https://{config_entry_setup.data[CONF_HOST]}:1234"
        f"/api/s/{config_entry_setup.data[CONF_SITE_ID]}/rest/device/mock-id",
    )

    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_off",
        {"entity_id": "switch.mock_name_port_1_poe"},
        blocking=True,
    )
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=5))
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 1
    assert aioclient_mock.mock_calls[0][2] == {
        "port_overrides": [{"poe_mode": "off", "port_idx": 1, "portconf_id": "1a1"}]
    }

    # Turn on PoE
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        {"entity_id": "switch.mock_name_port_1_poe"},
        blocking=True,
    )
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_off",
        {"entity_id": "switch.mock_name_port_2_poe"},
        blocking=True,
    )
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=5))
    await hass.async_block_till_done()
    assert aioclient_mock.call_count == 2
    assert aioclient_mock.mock_calls[1][2] == {
        "port_overrides": [
            {"poe_mode": "auto", "port_idx": 1, "portconf_id": "1a1"},
            {"poe_mode": "off", "port_idx": 2, "portconf_id": "1a2"},
        ]
    }

    # Device gets disabled
    device_1["disabled"] = True
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)
    await hass.async_block_till_done()
    assert hass.states.get("switch.mock_name_port_1_poe").state == STATE_UNAVAILABLE

    # Device gets re-enabled
    device_1["disabled"] = False
    mock_websocket_message(message=MessageKey.DEVICE, data=device_1)
    await hass.async_block_till_done()
    assert hass.states.get("switch.mock_name_port_1_poe").state == STATE_OFF