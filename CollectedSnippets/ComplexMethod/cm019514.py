async def test_sensors_flex(
    hass: HomeAssistant,
    canary,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the creation and values of the sensors for Canary Flex."""
    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Flex")

    instance = canary.return_value
    instance.get_locations.return_value = [
        mock_location(100, "Home", True, devices=[online_device_at_home]),
    ]

    instance.get_latest_readings.return_value = [
        mock_reading("battery", "70.4567"),
        mock_reading("wifi", "-57"),
    ]

    with patch("homeassistant.components.canary.PLATFORMS", ["sensor"]):
        await init_integration(hass)

    sensors = {
        "dining_room_home_dining_room_battery": (
            "20_battery",
            "70.46",
            PERCENTAGE,
            SensorDeviceClass.BATTERY,
            None,
        ),
        "dining_room_home_dining_room_wifi": (
            "20_wifi",
            "-57.0",
            SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            SensorDeviceClass.SIGNAL_STRENGTH,
            None,
        ),
    }

    for sensor_id, data in sensors.items():
        entity_entry = entity_registry.async_get(f"sensor.{sensor_id}")
        assert entity_entry
        assert entity_entry.original_device_class == data[3]
        assert entity_entry.unique_id == data[0]
        assert entity_entry.original_icon == data[4]

        state = hass.states.get(f"sensor.{sensor_id}")
        assert state
        assert state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) == data[2]
        assert state.state == data[1]

    device = device_registry.async_get_device(identifiers={(DOMAIN, "20")})
    assert device
    assert device.manufacturer == MANUFACTURER
    assert device.name == "Dining Room"
    assert device.model == "Canary Flex"