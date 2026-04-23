async def test_zha_logbook_event_device_no_triggers(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry, mock_devices
) -> None:
    """Test ZHA logbook events with device and without triggers."""

    _zigpy_device, zha_device = mock_devices
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
                    "device_ieee": str(ieee_address),
                    CONF_UNIQUE_ID: f"{ieee_address!s}:1:0x0006",
                    "endpoint_id": 1,
                    "cluster_id": 6,
                    "params": {},
                },
            ),
            MockRow(
                ZHA_EVENT,
                {
                    CONF_DEVICE_ID: reg_device.id,
                    "device_ieee": str(ieee_address),
                    CONF_UNIQUE_ID: f"{ieee_address!s}:1:0x0006",
                    "endpoint_id": 1,
                    "cluster_id": 6,
                },
            ),
            MockRow(
                ZHA_EVENT,
                {
                    CONF_DEVICE_ID: reg_device.id,
                    COMMAND: COMMAND_ATTRIBUTE_UPDATED,
                    "device_ieee": str(ieee_address),
                    CONF_UNIQUE_ID: f"{ieee_address!s}:1:0x0006",
                    "endpoint_id": 1,
                    "cluster_id": 6,
                    "args": {
                        "attribute_id": 1234,
                        "attribute_name": "name",
                        "attribute_value": "value",
                    },
                },
            ),
        ],
    )

    assert events[0]["name"] == "FakeManufacturer FakeModel"
    assert events[0]["domain"] == "zha"
    assert (
        events[0]["message"]
        == "Shake event was fired with parameters: {'test': 'test'}"
    )

    assert events[1]["name"] == "FakeManufacturer FakeModel"
    assert events[1]["domain"] == "zha"
    assert (
        events[1]["message"] == "Zha Event was fired with parameters: {'test': 'test'}"
    )

    assert events[2]["name"] == "FakeManufacturer FakeModel"
    assert events[2]["domain"] == "zha"
    assert events[2]["message"] == "Zha Event was fired"

    assert events[3]["name"] == "FakeManufacturer FakeModel"
    assert events[3]["domain"] == "zha"
    assert events[3]["message"] == "Zha Event was fired"

    assert events[4]["name"] == "FakeManufacturer FakeModel"
    assert events[4]["domain"] == "zha"
    assert (
        events[4]["message"]
        == "Attribute Updated event was fired with arguments: {'attribute_id': 1234, 'attribute_name': 'name', 'attribute_value': 'value'}"
    )