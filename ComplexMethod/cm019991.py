async def test_humanifying_deconz_alarm_event(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    sensor_payload: dict[str, Any],
) -> None:
    """Test humanifying deCONZ alarm event."""
    keypad_event_id = slugify(sensor_payload["name"])
    keypad_serial = serial_from_unique_id(sensor_payload["uniqueid"])
    keypad_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, keypad_serial)}
    )

    removed_device_event_id = "removed_device"
    removed_device_serial = "00:00:00:00:00:00:00:05"

    hass.config.components.add("recorder")
    assert await async_setup_component(hass, "logbook", {})
    await hass.async_block_till_done()

    events = mock_humanify(
        hass,
        [
            MockRow(
                CONF_DECONZ_ALARM_EVENT,
                {
                    CONF_CODE: 1234,
                    CONF_DEVICE_ID: keypad_entry.id,
                    CONF_EVENT: "armed_away",
                    CONF_ID: keypad_event_id,
                    CONF_UNIQUE_ID: keypad_serial,
                },
            ),
            # Event of a removed device
            MockRow(
                CONF_DECONZ_ALARM_EVENT,
                {
                    CONF_CODE: 1234,
                    CONF_DEVICE_ID: "ff99ff99ff99ff99ff99ff99ff99ff99",
                    CONF_EVENT: "armed_away",
                    CONF_ID: removed_device_event_id,
                    CONF_UNIQUE_ID: removed_device_serial,
                },
            ),
        ],
    )

    assert events[0]["name"] == "Keypad"
    assert events[0]["domain"] == "deconz"
    assert events[0]["message"] == "fired event 'armed_away'"

    assert events[1]["name"] == "removed_device"
    assert events[1]["domain"] == "deconz"
    assert events[1]["message"] == "fired event 'armed_away'"