async def test_update_entity_ha_not_running(
    hass: HomeAssistant,
    client: MagicMock,
    zen_31: Node,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test update occurs only after HA is running."""
    hass.set_state(CoreState.not_running)

    client.async_send_command.return_value = {"updates": []}

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    client.async_send_command.reset_mock()
    assert client.async_send_command.call_count == 0

    await hass.async_start()
    await hass.async_block_till_done()

    assert client.async_send_command.call_count == 0

    # Update should be delayed by a day because Home Assistant is not running
    hass.set_state(CoreState.starting)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15))
    await hass.async_block_till_done()

    assert client.async_send_command.call_count == 0

    hass.set_state(CoreState.running)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15, days=1))
    await hass.async_block_till_done()

    # Two nodes in total, the controller node and the zen_31 node.
    assert client.async_send_command.call_count == 2
    calls = sorted(
        client.async_send_command.call_args_list, key=lambda call: call[0][0]["nodeId"]
    )

    node_ids = (1, 94)
    for node_id, call in zip(node_ids, calls, strict=True):
        args = call[0][0]
        assert args["command"] == "controller.get_available_firmware_updates"
        assert args["nodeId"] == node_id