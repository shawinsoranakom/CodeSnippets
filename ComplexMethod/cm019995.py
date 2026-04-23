async def test_deconz_alarm_events(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    config_entry_setup: MockConfigEntry,
    sensor_ws_data: WebsocketDataType,
) -> None:
    """Test successful creation of deconz alarm events."""
    assert len(hass.states.async_all()) == 4
    # 1 alarm control device + 1 additional device for deconz gateway
    assert (
        len(
            dr.async_entries_for_config_entry(
                device_registry, config_entry_setup.entry_id
            )
        )
        == 2
    )

    captured_events = async_capture_events(hass, CONF_DECONZ_ALARM_EVENT)

    # Emergency event

    await sensor_ws_data({"state": {"action": AncillaryControlAction.EMERGENCY}})

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "00:00:00:00:00:00:00:01")}
    )

    assert len(captured_events) == 1
    assert captured_events[0].data == {
        CONF_ID: "keypad",
        CONF_UNIQUE_ID: "00:00:00:00:00:00:00:01",
        CONF_DEVICE_ID: device.id,
        CONF_EVENT: AncillaryControlAction.EMERGENCY.value,
    }

    # Fire event

    await sensor_ws_data({"state": {"action": AncillaryControlAction.FIRE}})

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "00:00:00:00:00:00:00:01")}
    )

    assert len(captured_events) == 2
    assert captured_events[1].data == {
        CONF_ID: "keypad",
        CONF_UNIQUE_ID: "00:00:00:00:00:00:00:01",
        CONF_DEVICE_ID: device.id,
        CONF_EVENT: AncillaryControlAction.FIRE.value,
    }

    # Invalid code event

    await sensor_ws_data({"state": {"action": AncillaryControlAction.INVALID_CODE}})

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "00:00:00:00:00:00:00:01")}
    )

    assert len(captured_events) == 3
    assert captured_events[2].data == {
        CONF_ID: "keypad",
        CONF_UNIQUE_ID: "00:00:00:00:00:00:00:01",
        CONF_DEVICE_ID: device.id,
        CONF_EVENT: AncillaryControlAction.INVALID_CODE.value,
    }

    # Panic event

    await sensor_ws_data({"state": {"action": AncillaryControlAction.PANIC}})

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "00:00:00:00:00:00:00:01")}
    )

    assert len(captured_events) == 4
    assert captured_events[3].data == {
        CONF_ID: "keypad",
        CONF_UNIQUE_ID: "00:00:00:00:00:00:00:01",
        CONF_DEVICE_ID: device.id,
        CONF_EVENT: AncillaryControlAction.PANIC.value,
    }

    # Only care for changes to specific action events

    await sensor_ws_data({"state": {"action": AncillaryControlAction.ARMED_AWAY}})
    assert len(captured_events) == 4

    # Only care for action events

    await sensor_ws_data({"state": {"panel": AncillaryControlPanel.ARMED_AWAY}})
    assert len(captured_events) == 4