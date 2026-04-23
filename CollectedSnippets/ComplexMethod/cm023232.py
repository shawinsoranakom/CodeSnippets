async def test_zwave_js_value_updated(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    client,
    lock_schlage_be469,
    integration,
) -> None:
    """Test for zwave_js.value_updated automation trigger."""
    trigger_type = f"{DOMAIN}.value_updated"
    node: Node = lock_schlage_be469
    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, lock_schlage_be469)}
    )
    assert device

    no_value_filter = async_capture_events(hass, "no_value_filter")
    single_from_value_filter = async_capture_events(hass, "single_from_value_filter")
    multiple_from_value_filters = async_capture_events(
        hass, "multiple_from_value_filters"
    )
    from_and_to_value_filters = async_capture_events(hass, "from_and_to_value_filters")
    different_value = async_capture_events(hass, "different_value")

    def clear_events():
        """Clear all events in the event list."""
        no_value_filter.clear()
        single_from_value_filter.clear()
        multiple_from_value_filters.clear()
        from_and_to_value_filters.clear()
        different_value.clear()

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                # no value filter
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                            "command_class": CommandClass.DOOR_LOCK.value,
                            "property": "latchStatus",
                        },
                    },
                    "action": {
                        "event": "no_value_filter",
                    },
                },
                # single from value filter
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "device_id": device.id,
                            "command_class": CommandClass.DOOR_LOCK.value,
                            "property": "latchStatus",
                            "from": "ajar",
                        },
                    },
                    "action": {
                        "event": "single_from_value_filter",
                    },
                },
                # multiple from value filters
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                            "command_class": CommandClass.DOOR_LOCK.value,
                            "property": "latchStatus",
                            "from": ["closed", "opened"],
                        },
                    },
                    "action": {
                        "event": "multiple_from_value_filters",
                    },
                },
                # from and to value filters
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                            "command_class": CommandClass.DOOR_LOCK.value,
                            "property": "latchStatus",
                            "from": ["closed", "opened"],
                            "to": ["opened"],
                        },
                    },
                    "action": {
                        "event": "from_and_to_value_filters",
                    },
                },
                # different value
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                            "command_class": CommandClass.DOOR_LOCK.value,
                            "property": "boltStatus",
                        },
                    },
                    "action": {
                        "event": "different_value",
                    },
                },
            ]
        },
    )

    # Test that no value filter is triggered
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Door Lock",
                "commandClass": 98,
                "endpoint": 0,
                "property": "latchStatus",
                "newValue": "boo",
                "prevValue": "hiss",
                "propertyName": "latchStatus",
            },
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    assert len(no_value_filter) == 1
    assert len(single_from_value_filter) == 0
    assert len(multiple_from_value_filters) == 0
    assert len(from_and_to_value_filters) == 0
    assert len(different_value) == 0

    clear_events()

    # Test that a single_from_value_filter is triggered
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Door Lock",
                "commandClass": 98,
                "endpoint": 0,
                "property": "latchStatus",
                "newValue": "boo",
                "prevValue": "ajar",
                "propertyName": "latchStatus",
            },
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    assert len(no_value_filter) == 1
    assert len(single_from_value_filter) == 1
    assert len(multiple_from_value_filters) == 0
    assert len(from_and_to_value_filters) == 0
    assert len(different_value) == 0

    clear_events()

    # Test that multiple_from_value_filters are triggered
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Door Lock",
                "commandClass": 98,
                "endpoint": 0,
                "property": "latchStatus",
                "newValue": "boo",
                "prevValue": "closed",
                "propertyName": "latchStatus",
            },
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    assert len(no_value_filter) == 1
    assert len(single_from_value_filter) == 0
    assert len(multiple_from_value_filters) == 1
    assert len(from_and_to_value_filters) == 0
    assert len(different_value) == 0

    clear_events()

    # Test that from_and_to_value_filters is triggered
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Door Lock",
                "commandClass": 98,
                "endpoint": 0,
                "property": "latchStatus",
                "newValue": "opened",
                "prevValue": "closed",
                "propertyName": "latchStatus",
            },
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    assert len(no_value_filter) == 1
    assert len(single_from_value_filter) == 0
    assert len(multiple_from_value_filters) == 1
    assert len(from_and_to_value_filters) == 1
    assert len(different_value) == 0

    clear_events()

    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Door Lock",
                "commandClass": 98,
                "endpoint": 0,
                "property": "boltStatus",
                "newValue": "boo",
                "prevValue": "hiss",
                "propertyName": "boltStatus",
            },
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    assert len(no_value_filter) == 0
    assert len(single_from_value_filter) == 0
    assert len(multiple_from_value_filters) == 0
    assert len(from_and_to_value_filters) == 0
    assert len(different_value) == 1

    clear_events()

    with patch("homeassistant.config.load_yaml_dict", return_value={}):
        await hass.services.async_call(automation.DOMAIN, SERVICE_RELOAD, blocking=True)