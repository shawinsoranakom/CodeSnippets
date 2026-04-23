async def test_zha_logbook_event_device_with_triggers(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry, mock_devices
) -> None:
    """Test ZHA logbook events with device and triggers."""

    zigpy_device, zha_device = mock_devices

    zigpy_device.device_automation_triggers = {
        (SHAKEN, SHAKEN): {COMMAND: COMMAND_SHAKE},
        (UP, DOUBLE_PRESS): {COMMAND: COMMAND_DOUBLE, "endpoint_id": 1},
        (DOWN, DOUBLE_PRESS): {COMMAND: COMMAND_DOUBLE, "endpoint_id": 2},
        (SHORT_PRESS, SHORT_PRESS): {COMMAND: COMMAND_SINGLE},
        (LONG_PRESS, LONG_PRESS): {COMMAND: COMMAND_HOLD},
        (LONG_RELEASE, LONG_RELEASE): {COMMAND: COMMAND_HOLD},
    }

    ieee_address = str(zha_device.device.ieee)

    reg_device = device_registry.async_get_device(identifiers={("zha", ieee_address)})

    hass.config.components.add("recorder")
    assert await async_setup_component(hass, "logbook", {})
    await hass.async_block_till_done()

    events = mock_humanify(
        hass,
        [
            MockRow(
                ZHA_EVENT,
                {
                    CONF_DEVICE_ID: reg_device.id,
                    COMMAND: COMMAND_SHAKE,
                    "device_ieee": str(ieee_address),
                    CONF_UNIQUE_ID: f"{ieee_address!s}:1:0x0006",
                    "endpoint_id": 1,
                    "cluster_id": 6,
                    "params": {
                        "test": "test",
                    },
                },
            ),
            MockRow(
                ZHA_EVENT,
                {
                    CONF_DEVICE_ID: reg_device.id,
                    COMMAND: COMMAND_DOUBLE,
                    "device_ieee": str(ieee_address),
                    CONF_UNIQUE_ID: f"{ieee_address!s}:1:0x0006",
                    "endpoint_id": 1,
                    "cluster_id": 6,
                    "params": {
                        "test": "test",
                    },
                },
            ),
            MockRow(
                ZHA_EVENT,
                {
                    CONF_DEVICE_ID: reg_device.id,
                    COMMAND: COMMAND_DOUBLE,
                    "device_ieee": str(ieee_address),
                    CONF_UNIQUE_ID: f"{ieee_address!s}:1:0x0006",
                    "endpoint_id": 2,
                    "cluster_id": 6,
                    "params": {
                        "test": "test",
                    },
                },
            ),
        ],
    )

    assert events[0]["name"] == "FakeManufacturer FakeModel"
    assert events[0]["domain"] == "zha"
    assert (
        events[0]["message"]
        == "Device Shaken event was fired with parameters: {'test': 'test'}"
    )

    assert events[1]["name"] == "FakeManufacturer FakeModel"
    assert events[1]["domain"] == "zha"
    assert events[1]["message"] == (
        "Up - Remote Button Double Press event was fired with parameters: "
        "{'test': 'test'}"
    )