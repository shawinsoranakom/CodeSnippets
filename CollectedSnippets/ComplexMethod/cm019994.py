async def test_deconz_events(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    config_entry_setup: MockConfigEntry,
    sensor_ws_data: WebsocketDataType,
) -> None:
    """Test successful creation of deconz events."""
    assert len(hass.states.async_all()) == 3
    # 5 switches + 1 additional device for deconz gateway
    assert (
        len(
            dr.async_entries_for_config_entry(
                device_registry, config_entry_setup.entry_id
            )
        )
        == 6
    )
    assert hass.states.get("sensor.switch_2_battery").state == "100"
    assert hass.states.get("sensor.switch_3_battery").state == "100"
    assert hass.states.get("sensor.switch_4_battery").state == "100"

    captured_events = async_capture_events(hass, CONF_DECONZ_EVENT)

    await sensor_ws_data({"id": "1", "state": {"buttonevent": 2000}})

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "00:00:00:00:00:00:00:01")}
    )

    assert len(captured_events) == 1
    assert captured_events[0].data == {
        "id": "switch_1",
        "unique_id": "00:00:00:00:00:00:00:01",
        "event": 2000,
        "device_id": device.id,
    }

    await sensor_ws_data({"id": "3", "state": {"buttonevent": 2000}})

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "00:00:00:00:00:00:00:03")}
    )

    assert len(captured_events) == 2
    assert captured_events[1].data == {
        "id": "switch_3",
        "unique_id": "00:00:00:00:00:00:00:03",
        "event": 2000,
        "gesture": 1,
        "device_id": device.id,
    }

    await sensor_ws_data({"id": "4", "state": {"gesture": 0}})

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "00:00:00:00:00:00:00:04")}
    )

    assert len(captured_events) == 3
    assert captured_events[2].data == {
        "id": "switch_4",
        "unique_id": "00:00:00:00:00:00:00:04",
        "event": 1000,
        "gesture": 0,
        "device_id": device.id,
    }

    event_changed_sensor = {
        "id": "5",
        "state": {"buttonevent": 6002, "angle": 110, "xy": [0.5982, 0.3897]},
    }
    await sensor_ws_data(event_changed_sensor)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "00:00:00:00:00:00:00:05")}
    )

    assert len(captured_events) == 4
    assert captured_events[3].data == {
        "id": "zha_remote_1",
        "unique_id": "00:00:00:00:00:00:00:05",
        "event": 6002,
        "angle": 110,
        "xy": [0.5982, 0.3897],
        "device_id": device.id,
    }

    # Unsupported event

    await sensor_ws_data({"id": "1", "name": "other name"})
    assert len(captured_events) == 4