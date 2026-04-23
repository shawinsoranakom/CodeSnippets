async def test_zwave_js_event(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    client,
    lock_schlage_be469,
    integration,
) -> None:
    """Test for zwave_js.event automation trigger."""
    trigger_type = f"{DOMAIN}.event"
    node: Node = lock_schlage_be469
    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, lock_schlage_be469)}
    )
    assert device

    node_no_event_data_filter = async_capture_events(hass, "node_no_event_data_filter")
    node_event_data_filter = async_capture_events(hass, "node_event_data_filter")
    controller_no_event_data_filter = async_capture_events(
        hass, "controller_no_event_data_filter"
    )
    controller_event_data_filter = async_capture_events(
        hass, "controller_event_data_filter"
    )
    driver_no_event_data_filter = async_capture_events(
        hass, "driver_no_event_data_filter"
    )
    driver_event_data_filter = async_capture_events(hass, "driver_event_data_filter")
    node_event_data_no_partial_dict_match_filter = async_capture_events(
        hass, "node_event_data_no_partial_dict_match_filter"
    )
    node_event_data_partial_dict_match_filter = async_capture_events(
        hass, "node_event_data_partial_dict_match_filter"
    )

    def clear_events():
        """Clear all events in the event list."""
        node_no_event_data_filter.clear()
        node_event_data_filter.clear()
        controller_no_event_data_filter.clear()
        controller_event_data_filter.clear()
        driver_no_event_data_filter.clear()
        driver_event_data_filter.clear()
        node_event_data_no_partial_dict_match_filter.clear()
        node_event_data_partial_dict_match_filter.clear()

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                # node filter: no event data
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                            "event_source": "node",
                            "event": "interview stage completed",
                        },
                    },
                    "action": {
                        "event": "node_no_event_data_filter",
                    },
                },
                # node filter: event data
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "device_id": device.id,
                            "event_source": "node",
                            "event": "interview stage completed",
                            "event_data": {"stageName": "ProtocolInfo"},
                        },
                    },
                    "action": {
                        "event": "node_event_data_filter",
                    },
                },
                # controller filter: no event data
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "config_entry_id": integration.entry_id,
                            "event_source": "controller",
                            "event": "inclusion started",
                        },
                    },
                    "action": {
                        "event": "controller_no_event_data_filter",
                    },
                },
                # controller filter: event data
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "config_entry_id": integration.entry_id,
                            "event_source": "controller",
                            "event": "inclusion started",
                            "event_data": {"strategy": 0},
                        },
                    },
                    "action": {
                        "event": "controller_event_data_filter",
                    },
                },
                # driver filter: no event data
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "config_entry_id": integration.entry_id,
                            "event_source": "driver",
                            "event": "logging",
                        },
                    },
                    "action": {
                        "event": "driver_no_event_data_filter",
                    },
                },
                # driver filter: event data
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "config_entry_id": integration.entry_id,
                            "event_source": "driver",
                            "event": "logging",
                            "event_data": {"message": "test"},
                        },
                    },
                    "action": {
                        "event": "driver_event_data_filter",
                    },
                },
                # node filter: event data, no partial dict match
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                            "event_source": "node",
                            "event": "value updated",
                            "event_data": {"args": {"commandClassName": "Door Lock"}},
                        },
                    },
                    "action": {
                        "event": "node_event_data_no_partial_dict_match_filter",
                    },
                },
                # node filter: event data, partial dict match
                {
                    "trigger": {
                        "platform": trigger_type,
                        "options": {
                            "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                            "event_source": "node",
                            "event": "value updated",
                            "event_data": {"args": {"commandClassName": "Door Lock"}},
                            "partial_dict_match": True,
                        },
                    },
                    "action": {
                        "event": "node_event_data_partial_dict_match_filter",
                    },
                },
            ]
        },
    )

    # Test that `node no event data filter` is triggered and `node event data
    # filter` is not
    event = Event(
        type="interview stage completed",
        data={
            "source": "node",
            "event": "interview stage completed",
            "stageName": "NodeInfo",
            "nodeId": node.node_id,
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    assert len(node_no_event_data_filter) == 1
    assert len(node_event_data_filter) == 0
    assert len(controller_no_event_data_filter) == 0
    assert len(controller_event_data_filter) == 0
    assert len(driver_no_event_data_filter) == 0
    assert len(driver_event_data_filter) == 0
    assert len(node_event_data_no_partial_dict_match_filter) == 0
    assert len(node_event_data_partial_dict_match_filter) == 0

    clear_events()

    # Test that `node no event data filter` and `node event data filter` are triggered
    event = Event(
        type="interview stage completed",
        data={
            "source": "node",
            "event": "interview stage completed",
            "stageName": "ProtocolInfo",
            "nodeId": node.node_id,
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    assert len(node_no_event_data_filter) == 1
    assert len(node_event_data_filter) == 1
    assert len(controller_no_event_data_filter) == 0
    assert len(controller_event_data_filter) == 0
    assert len(driver_no_event_data_filter) == 0
    assert len(driver_event_data_filter) == 0
    assert len(node_event_data_no_partial_dict_match_filter) == 0
    assert len(node_event_data_partial_dict_match_filter) == 0

    clear_events()

    # Test that `controller no event data filter` is triggered and `controller event
    # data filter` is not
    event = Event(
        type="inclusion started",
        data={
            "source": "controller",
            "event": "inclusion started",
            "strategy": 2,
        },
    )
    client.driver.controller.receive_event(event)
    await hass.async_block_till_done()

    assert len(node_no_event_data_filter) == 0
    assert len(node_event_data_filter) == 0
    assert len(controller_no_event_data_filter) == 1
    assert len(controller_event_data_filter) == 0
    assert len(driver_no_event_data_filter) == 0
    assert len(driver_event_data_filter) == 0
    assert len(node_event_data_no_partial_dict_match_filter) == 0
    assert len(node_event_data_partial_dict_match_filter) == 0

    clear_events()

    # Test that both `controller no event data filter` and `controller event data
    # filter`` are triggered
    event = Event(
        type="inclusion started",
        data={
            "source": "controller",
            "event": "inclusion started",
            "strategy": 0,
        },
    )
    client.driver.controller.receive_event(event)
    await hass.async_block_till_done()

    assert len(node_no_event_data_filter) == 0
    assert len(node_event_data_filter) == 0
    assert len(controller_no_event_data_filter) == 1
    assert len(controller_event_data_filter) == 1
    assert len(driver_no_event_data_filter) == 0
    assert len(driver_event_data_filter) == 0
    assert len(node_event_data_no_partial_dict_match_filter) == 0
    assert len(node_event_data_partial_dict_match_filter) == 0

    clear_events()

    # Test that `driver no event data filter` is triggered and `driver event data
    # filter` is not
    event = Event(
        type="logging",
        data={
            "source": "driver",
            "event": "logging",
            "message": "no test",
            "formattedMessage": "test",
            "direction": ">",
            "level": "debug",
            "primaryTags": "tag",
            "secondaryTags": "tag2",
            "secondaryTagPadding": 0,
            "multiline": False,
            "timestamp": "time",
            "label": "label",
            "context": {"source": "config"},
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    assert len(node_no_event_data_filter) == 0
    assert len(node_event_data_filter) == 0
    assert len(controller_no_event_data_filter) == 0
    assert len(controller_event_data_filter) == 0
    assert len(driver_no_event_data_filter) == 1
    assert len(driver_event_data_filter) == 0
    assert len(node_event_data_no_partial_dict_match_filter) == 0
    assert len(node_event_data_partial_dict_match_filter) == 0

    clear_events()

    # Test that both `driver no event data filter` and `driver event data filter`
    # are triggered
    event = Event(
        type="logging",
        data={
            "source": "driver",
            "event": "logging",
            "message": "test",
            "formattedMessage": "test",
            "direction": ">",
            "level": "debug",
            "primaryTags": "tag",
            "secondaryTags": "tag2",
            "secondaryTagPadding": 0,
            "multiline": False,
            "timestamp": "time",
            "label": "label",
            "context": {"source": "config"},
        },
    )
    client.driver.receive_event(event)
    await hass.async_block_till_done()

    assert len(node_no_event_data_filter) == 0
    assert len(node_event_data_filter) == 0
    assert len(controller_no_event_data_filter) == 0
    assert len(controller_event_data_filter) == 0
    assert len(driver_no_event_data_filter) == 1
    assert len(driver_event_data_filter) == 1
    assert len(node_event_data_no_partial_dict_match_filter) == 0
    assert len(node_event_data_partial_dict_match_filter) == 0

    clear_events()

    # Test that only `node with event data and partial match dict filter` is triggered
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "Door Lock",
                "commandClass": 49,
                "endpoint": 0,
                "property": "latchStatus",
                "newValue": "closed",
                "prevValue": "open",
                "propertyName": "latchStatus",
            },
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    assert len(node_no_event_data_filter) == 0
    assert len(node_event_data_filter) == 0
    assert len(controller_no_event_data_filter) == 0
    assert len(controller_event_data_filter) == 0
    assert len(driver_no_event_data_filter) == 0
    assert len(driver_event_data_filter) == 0
    assert len(node_event_data_no_partial_dict_match_filter) == 0
    assert len(node_event_data_partial_dict_match_filter) == 1

    clear_events()

    # Test that `node with event data and partial match dict filter` is not triggered
    # when partial dict doesn't match
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": node.node_id,
            "args": {
                "commandClassName": "fake command class name",
                "commandClass": 49,
                "endpoint": 0,
                "property": "latchStatus",
                "newValue": "closed",
                "prevValue": "open",
                "propertyName": "latchStatus",
            },
        },
    )
    node.receive_event(event)
    await hass.async_block_till_done()

    assert len(node_no_event_data_filter) == 0
    assert len(node_event_data_filter) == 0
    assert len(controller_no_event_data_filter) == 0
    assert len(controller_event_data_filter) == 0
    assert len(driver_no_event_data_filter) == 0
    assert len(driver_event_data_filter) == 0
    assert len(node_event_data_no_partial_dict_match_filter) == 0
    assert len(node_event_data_partial_dict_match_filter) == 0

    clear_events()

    with patch("homeassistant.config.load_yaml_dict", return_value={}):
        await hass.services.async_call(automation.DOMAIN, SERVICE_RELOAD, blocking=True)