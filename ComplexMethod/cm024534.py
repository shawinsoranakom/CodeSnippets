async def test_set_sensors_used_in_climate(hass: HomeAssistant) -> None:
    """Test set sensors used in climate."""
    # Get device_id of remote sensor from the device registry.
    await setup_platform(hass, [const.Platform.CLIMATE, const.Platform.SENSOR])
    device_registry = dr.async_get(hass)
    for device in device_registry.devices.values():
        if device.name == "Remote Sensor 1":
            remote_sensor_1_id = device.id
        if device.name == "ecobee":
            ecobee_id = device.id
        if device.name == "Remote Sensor 2":
            remote_sensor_2_id = device.id

    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)
    device_from_other_integration = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={("test", "unique")}
    )

    # Test that the function call works in its entirety.
    with mock.patch("pyecobee.Ecobee.update_climate_sensors") as mock_sensors:
        await hass.services.async_call(
            DOMAIN,
            "set_sensors_used_in_climate",
            {
                ATTR_ENTITY_ID: ENTITY_ID,
                ATTR_PRESET_MODE: "Climate1",
                ATTR_SENSOR_LIST: [remote_sensor_1_id],
            },
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_sensors.assert_called_once_with(0, "Climate1", sensor_ids=["rs:100"])

    # Update sensors without preset mode.
    with mock.patch("pyecobee.Ecobee.update_climate_sensors") as mock_sensors:
        await hass.services.async_call(
            DOMAIN,
            "set_sensors_used_in_climate",
            {
                ATTR_ENTITY_ID: ENTITY_ID,
                ATTR_SENSOR_LIST: [remote_sensor_1_id],
            },
            blocking=True,
        )
        await hass.async_block_till_done()
        # `temp` is the preset running because of a hold.
        mock_sensors.assert_called_once_with(0, "temp", sensor_ids=["rs:100"])

    # Check that sensors are not updated when the sent sensors are the currently set sensors.
    with mock.patch("pyecobee.Ecobee.update_climate_sensors") as mock_sensors:
        await hass.services.async_call(
            DOMAIN,
            "set_sensors_used_in_climate",
            {
                ATTR_ENTITY_ID: ENTITY_ID,
                ATTR_PRESET_MODE: "Climate1",
                ATTR_SENSOR_LIST: [ecobee_id],
            },
            blocking=True,
        )
        mock_sensors.assert_not_called()

    # Error raised because invalid climate name.
    with pytest.raises(ServiceValidationError) as execinfo:
        await hass.services.async_call(
            DOMAIN,
            "set_sensors_used_in_climate",
            {
                ATTR_ENTITY_ID: ENTITY_ID,
                ATTR_PRESET_MODE: "InvalidClimate",
                ATTR_SENSOR_LIST: [remote_sensor_1_id],
            },
            blocking=True,
        )
    assert execinfo.value.translation_domain == "ecobee"
    assert execinfo.value.translation_key == "invalid_preset"

    ## Error raised because invalid sensor.
    with pytest.raises(ServiceValidationError) as execinfo:
        await hass.services.async_call(
            DOMAIN,
            "set_sensors_used_in_climate",
            {
                ATTR_ENTITY_ID: ENTITY_ID,
                ATTR_PRESET_MODE: "Climate1",
                ATTR_SENSOR_LIST: ["abcd"],
            },
            blocking=True,
        )
    assert execinfo.value.translation_domain == "ecobee"
    assert execinfo.value.translation_key == "invalid_sensor"

    ## Error raised because sensor not available on device.
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "set_sensors_used_in_climate",
            {
                ATTR_ENTITY_ID: ENTITY_ID,
                ATTR_PRESET_MODE: "Climate1",
                ATTR_SENSOR_LIST: [remote_sensor_2_id],
            },
            blocking=True,
        )

    with pytest.raises(ServiceValidationError) as execinfo:
        await hass.services.async_call(
            DOMAIN,
            "set_sensors_used_in_climate",
            {
                ATTR_ENTITY_ID: ENTITY_ID,
                ATTR_PRESET_MODE: "Climate1",
                ATTR_SENSOR_LIST: [
                    remote_sensor_1_id,
                    device_from_other_integration.id,
                ],
            },
            blocking=True,
        )
    assert execinfo.value.translation_domain == "ecobee"
    assert execinfo.value.translation_key == "sensor_lookup_failed"