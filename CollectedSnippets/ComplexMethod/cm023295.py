async def test_update_entity_delay(
    hass: HomeAssistant,
    client: MagicMock,
    ge_in_wall_dimmer_switch: Node,
    zen_31: Node,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test update occurs on a delay after HA starts."""
    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"updates": []}
    hass.set_state(CoreState.not_running)

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    client.async_send_command.reset_mock()
    assert client.async_send_command.call_count == 0

    await hass.async_start()
    await hass.async_block_till_done()

    assert client.async_send_command.call_count == 0

    update_interval = timedelta(seconds=15)
    freezer.tick(update_interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    nodes: set[int] = set()

    assert client.async_send_command.call_count == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "controller.get_available_firmware_updates"
    nodes.add(args["nodeId"])

    freezer.tick(update_interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert client.async_send_command.call_count == 2
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "controller.get_available_firmware_updates"
    nodes.add(args["nodeId"])

    freezer.tick(update_interval)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert client.async_send_command.call_count == 3
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "controller.get_available_firmware_updates"
    nodes.add(args["nodeId"])

    assert len(nodes) == 3
    assert nodes == {1, ge_in_wall_dimmer_switch.node_id, zen_31.node_id}