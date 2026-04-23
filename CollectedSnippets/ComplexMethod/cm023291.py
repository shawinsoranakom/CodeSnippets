async def test_update_entity_update_failure(
    hass: HomeAssistant,
    client: MagicMock,
    climate_radio_thermostat_ct100_plus_different_endpoints: Node,
    integration: MockConfigEntry,
) -> None:
    """Test update entity update failed."""
    assert client.async_send_command.call_count == 0
    client.async_send_command.side_effect = FailedZWaveCommand("test", 260, "test")

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15, days=1))
    await hass.async_block_till_done()

    entity_ids = (CONTROLLER_UPDATE_ENTITY, NODE_UPDATE_ENTITY)
    for entity_id in entity_ids:
        state = hass.states.get(entity_id)
        assert state
        assert state.state == STATE_OFF

    assert client.async_send_command.call_count == 2
    calls = sorted(
        client.async_send_command.call_args_list, key=lambda call: call[0][0]["nodeId"]
    )

    node_ids = (1, 26)
    for node_id, call in zip(node_ids, calls, strict=True):
        args = call[0][0]
        assert args["command"] == "controller.get_available_firmware_updates"
        assert args["nodeId"] == node_id