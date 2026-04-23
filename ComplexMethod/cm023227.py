async def test_humanifying_zwave_js_notification_event(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    client,
    lock_schlage_be469,
    integration,
) -> None:
    """Test humanifying Z-Wave JS notification events."""
    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, lock_schlage_be469)}
    )
    assert device

    hass.config.components.add("recorder")
    assert await async_setup_component(hass, "logbook", {})
    await hass.async_block_till_done()

    events = mock_humanify(
        hass,
        [
            MockRow(
                ZWAVE_JS_NOTIFICATION_EVENT,
                {
                    "device_id": device.id,
                    "command_class": CommandClass.NOTIFICATION.value,
                    "command_class_name": "Notification",
                    "label": "label",
                    "event_label": "event_label",
                },
            ),
            MockRow(
                ZWAVE_JS_NOTIFICATION_EVENT,
                {
                    "device_id": device.id,
                    "command_class": CommandClass.ENTRY_CONTROL.value,
                    "command_class_name": "Entry Control",
                    "event_type": 1,
                    "data_type": 2,
                },
            ),
            MockRow(
                ZWAVE_JS_NOTIFICATION_EVENT,
                {
                    "device_id": device.id,
                    "command_class": CommandClass.SWITCH_MULTILEVEL.value,
                    "command_class_name": "Multilevel Switch",
                    "event_type": 1,
                    "direction": "up",
                },
            ),
            MockRow(
                ZWAVE_JS_NOTIFICATION_EVENT,
                {
                    "device_id": device.id,
                    "command_class": CommandClass.POWERLEVEL.value,
                    "command_class_name": "Powerlevel",
                },
            ),
        ],
    )

    assert events[0]["name"] == "Touchscreen Deadbolt"
    assert events[0]["domain"] == "zwave_js"
    assert (
        events[0]["message"]
        == "fired Notification CC 'notification' event 'label': 'event_label'"
    )

    assert events[1]["name"] == "Touchscreen Deadbolt"
    assert events[1]["domain"] == "zwave_js"
    assert events[1]["message"] == (
        "fired Entry Control CC 'notification' event for event type '1' "
        "with data type '2'"
    )

    assert events[2]["name"] == "Touchscreen Deadbolt"
    assert events[2]["domain"] == "zwave_js"
    assert (
        events[2]["message"]
        == "fired Multilevel Switch CC 'notification' event for event type '1': 'up'"
    )

    assert events[3]["name"] == "Touchscreen Deadbolt"
    assert events[3]["domain"] == "zwave_js"
    assert events[3]["message"] == "fired Powerlevel CC 'notification' event"