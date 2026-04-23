async def test_identify_event(
    hass: HomeAssistant,
    client: MagicMock,
    multisensor_6: Node,
    integration: MockConfigEntry,
) -> None:
    """Test controller identify event."""
    # One config entry scenario
    event = Event(
        type="identify",
        data={
            "source": "controller",
            "event": "identify",
            "nodeId": multisensor_6.node_id,
        },
    )
    dev_id = get_device_id(client.driver, multisensor_6)
    msg_id = f"{DOMAIN}.identify_controller.{dev_id[1]}"

    client.driver.controller.receive_event(event)
    notifications = async_get_persistent_notifications(hass)
    assert len(notifications) == 1
    assert list(notifications)[0] == msg_id
    assert notifications[msg_id]["message"].startswith("`Multisensor 6`")
    assert "with the home ID" not in notifications[msg_id]["message"]
    async_dismiss(hass, msg_id)

    # Add mock config entry to simulate having multiple entries
    new_entry = MockConfigEntry(domain=DOMAIN)
    new_entry.add_to_hass(hass)

    # Test case where config entry title and home ID don't match
    client.driver.controller.receive_event(event)
    notifications = async_get_persistent_notifications(hass)
    assert len(notifications) == 1
    assert list(notifications)[0] == msg_id
    assert (
        "network `Mock Title`, with the home ID `0xc16d02a3`"
        in notifications[msg_id]["message"]
    )
    async_dismiss(hass, msg_id)

    # Test case where config entry title and home ID do match
    hass.config_entries.async_update_entry(integration, title="0xc16d02a3")
    client.driver.controller.receive_event(event)
    notifications = async_get_persistent_notifications(hass)
    assert len(notifications) == 1
    assert list(notifications)[0] == msg_id
    assert "network with the home ID `0xc16d02a3`" in notifications[msg_id]["message"]