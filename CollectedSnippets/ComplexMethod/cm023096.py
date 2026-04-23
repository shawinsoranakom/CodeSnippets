async def test_factory_reset_node(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    client: MagicMock,
    multisensor_6: Node,
    multisensor_6_state: NodeDataType,
    integration: MockConfigEntry,
) -> None:
    """Test when a node is removed because it was reset."""
    # One config entry scenario
    remove_event = Event(
        type="node removed",
        data={
            "source": "controller",
            "event": "node removed",
            "reason": 5,
            "node": deepcopy(multisensor_6_state),
        },
    )
    dev_id = get_device_id(client.driver, multisensor_6)
    msg_id = f"{DOMAIN}.node_reset_and_removed.{dev_id[1]}"

    client.driver.controller.receive_event(remove_event)
    notifications = async_get_persistent_notifications(hass)
    assert len(notifications) == 1
    assert list(notifications)[0] == msg_id
    assert notifications[msg_id]["message"].startswith("`Multisensor 6`")
    assert "with the home ID" not in notifications[msg_id]["message"]
    async_dismiss(hass, msg_id)
    await hass.async_block_till_done()
    assert not device_registry.async_get_device(identifiers={dev_id})

    # Add mock config entry to simulate having multiple entries
    new_entry = MockConfigEntry(domain=DOMAIN)
    new_entry.add_to_hass(hass)

    # Re-add the node then remove it again
    add_event = Event(
        type="node added",
        data={
            "source": "controller",
            "event": "node added",
            "node": deepcopy(multisensor_6_state),
            "result": {},
        },
    )
    client.driver.controller.receive_event(add_event)
    await hass.async_block_till_done()
    remove_event.data["node"] = deepcopy(multisensor_6_state)
    client.driver.controller.receive_event(remove_event)
    # Test case where config entry title and home ID don't match
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
    add_event = Event(
        type="node added",
        data={
            "source": "controller",
            "event": "node added",
            "node": deepcopy(multisensor_6_state),
            "result": {},
        },
    )
    client.driver.controller.receive_event(add_event)
    await hass.async_block_till_done()
    remove_event.data["node"] = deepcopy(multisensor_6_state)
    client.driver.controller.receive_event(remove_event)
    notifications = async_get_persistent_notifications(hass)
    assert len(notifications) == 1
    assert list(notifications)[0] == msg_id
    assert "network with the home ID `0xc16d02a3`" in notifications[msg_id]["message"]