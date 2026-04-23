async def test_setup_all_platforms(
    hass: HomeAssistant,
    mock_miele_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    load_device_file: str,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that all platforms can be set up."""

    await setup_integration(hass, mock_config_entry)

    assert hass.states.get("binary_sensor.freezer_door").state == "off"
    assert hass.states.get("binary_sensor.hood_problem").state == "off"

    assert (
        hass.states.get("button.washing_machine_start").object_id
        == "washing_machine_start"
    )

    assert hass.states.get("climate.freezer").state == "cool"
    assert hass.states.get("light.hood_light").state == "on"

    assert hass.states.get("sensor.freezer_temperature").state == "-18.0"
    assert hass.states.get("sensor.washing_machine").state == "off"

    assert hass.states.get("switch.washing_machine_power").state == "off"

    # Add two devices and let the clock tick for 130 seconds
    mock_miele_client.get_devices.return_value = await async_load_json_object_fixture(
        hass, "5_devices.json", DOMAIN
    )
    freezer.tick(timedelta(seconds=130))

    prev_devices = len(device_registry.devices)

    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert len(device_registry.devices) == prev_devices + 1

    # Check a sample sensor for each new device
    assert hass.states.get("sensor.dishwasher").state == "in_use"
    assert hass.states.get("sensor.oven_temperature_2").state == "175.0"