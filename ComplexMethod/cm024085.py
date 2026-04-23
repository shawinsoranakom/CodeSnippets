async def test_notify_sensor(hass: HomeAssistant) -> None:
    """Test setting up a notify sensor."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="62:00:A1:3C:AE:7B",
        data={CONF_DEVICE_TYPE: "IAM-T1"},
    )
    entry.add_to_hass(hass)
    inject_bluetooth_service_info(hass, IAM_T1_SERVICE_INFO)
    saved_update_callback = None
    saved_device_data_changed_callback = None

    class MockINKBIRDBluetoothDeviceData(INKBIRDBluetoothDeviceData):
        def __init__(
            self,
            device_type: Model | str | None = None,
            device_data: dict[str, Any] | None = None,
            update_callback: Callable[[SensorUpdate], None] | None = None,
            device_data_changed_callback: Callable[[dict[str, Any]], None]
            | None = None,
        ) -> None:
            nonlocal saved_update_callback
            nonlocal saved_device_data_changed_callback
            saved_update_callback = update_callback
            saved_device_data_changed_callback = device_data_changed_callback
            super().__init__(
                device_type=device_type,
                device_data=device_data,
                update_callback=update_callback,
                device_data_changed_callback=device_data_changed_callback,
            )

    mock_client = MagicMock(start_notify=AsyncMock(), disconnect=AsyncMock())
    with (
        patch(
            "homeassistant.components.inkbird.coordinator.INKBIRDBluetoothDeviceData",
            MockINKBIRDBluetoothDeviceData,
        ),
        patch("inkbird_ble.parser.establish_connection", return_value=mock_client),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert len(hass.states.async_all()) == 0

    saved_update_callback(_make_sensor_update("IAM-T1", 10.24))

    assert len(hass.states.async_all()) == 1

    temp_sensor = hass.states.get("sensor.iam_t1_eeff_humidity")
    temp_sensor_attribtes = temp_sensor.attributes
    assert temp_sensor.state == "10.24"
    assert temp_sensor_attribtes[ATTR_FRIENDLY_NAME] == "IAM-T1 EEFF Humidity"
    assert temp_sensor_attribtes[ATTR_UNIT_OF_MEASUREMENT] == "%"
    assert temp_sensor_attribtes[ATTR_STATE_CLASS] == "measurement"

    assert entry.data[CONF_DEVICE_TYPE] == "IAM-T1"

    saved_device_data_changed_callback({"temp_unit": "F"})
    assert entry.data[CONF_DEVICE_DATA] == {"temp_unit": "F"}

    saved_device_data_changed_callback({"temp_unit": "C"})
    assert entry.data[CONF_DEVICE_DATA] == {"temp_unit": "C"}

    saved_device_data_changed_callback({"temp_unit": "C"})
    assert entry.data[CONF_DEVICE_DATA] == {"temp_unit": "C"}