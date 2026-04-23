async def test_humanifying_deconz_event(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    sensor_payload: dict[str, Any],
) -> None:
    """Test humanifying deCONZ event."""
    switch_event_id = slugify(sensor_payload["1"]["name"])
    switch_serial = serial_from_unique_id(sensor_payload["1"]["uniqueid"])
    switch_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, switch_serial)}
    )

    hue_remote_event_id = slugify(sensor_payload["2"]["name"])
    hue_remote_serial = serial_from_unique_id(sensor_payload["2"]["uniqueid"])
    hue_remote_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, hue_remote_serial)}
    )

    xiaomi_cube_event_id = slugify(sensor_payload["3"]["name"])
    xiaomi_cube_serial = serial_from_unique_id(sensor_payload["3"]["uniqueid"])
    xiaomi_cube_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, xiaomi_cube_serial)}
    )

    faulty_event_id = slugify(sensor_payload["4"]["name"])
    faulty_serial = serial_from_unique_id(sensor_payload["4"]["uniqueid"])
    faulty_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, faulty_serial)}
    )

    removed_device_event_id = "removed_device"
    removed_device_serial = "00:00:00:00:00:00:00:05"

    hass.config.components.add("recorder")
    assert await async_setup_component(hass, "logbook", {})
    await hass.async_block_till_done()

    events = mock_humanify(
        hass,
        [
            # Event without matching device trigger
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: switch_entry.id,
                    CONF_EVENT: 2000,
                    CONF_ID: switch_event_id,
                    CONF_UNIQUE_ID: switch_serial,
                },
            ),
            # Event with matching device trigger
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: hue_remote_entry.id,
                    CONF_EVENT: 2001,
                    CONF_ID: hue_remote_event_id,
                    CONF_UNIQUE_ID: hue_remote_serial,
                },
            ),
            # Gesture with matching device trigger
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: xiaomi_cube_entry.id,
                    CONF_GESTURE: 1,
                    CONF_ID: xiaomi_cube_event_id,
                    CONF_UNIQUE_ID: xiaomi_cube_serial,
                },
            ),
            # Unsupported device trigger
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: xiaomi_cube_entry.id,
                    CONF_GESTURE: "unsupported_gesture",
                    CONF_ID: xiaomi_cube_event_id,
                    CONF_UNIQUE_ID: xiaomi_cube_serial,
                },
            ),
            # Unknown event
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: faulty_entry.id,
                    "unknown_event": None,
                    CONF_ID: faulty_event_id,
                    CONF_UNIQUE_ID: faulty_serial,
                },
            ),
            # Event of a removed device
            MockRow(
                CONF_DECONZ_EVENT,
                {
                    CONF_DEVICE_ID: "ff99ff99ff99ff99ff99ff99ff99ff99",
                    CONF_EVENT: 2000,
                    CONF_ID: removed_device_event_id,
                    CONF_UNIQUE_ID: removed_device_serial,
                },
            ),
        ],
    )

    assert events[0]["name"] == "Switch 1"
    assert events[0]["domain"] == "deconz"
    assert events[0]["message"] == "fired event '2000'"

    assert events[1]["name"] == "Hue remote"
    assert events[1]["domain"] == "deconz"
    assert events[1]["message"] == "'Long press' event for 'Dim up' was fired"

    assert events[2]["name"] == "Xiaomi cube"
    assert events[2]["domain"] == "deconz"
    assert events[2]["message"] == "fired event 'Shake'"

    assert events[3]["name"] == "Xiaomi cube"
    assert events[3]["domain"] == "deconz"
    assert events[3]["message"] == "fired event 'unsupported_gesture'"

    assert events[4]["name"] == "Faulty event"
    assert events[4]["domain"] == "deconz"
    assert events[4]["message"] == "fired an unknown event"

    assert events[5]["name"] == "removed_device"
    assert events[5]["domain"] == "deconz"
    assert events[5]["message"] == "fired event '2000'"