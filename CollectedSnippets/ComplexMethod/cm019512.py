async def test_sensors_pro(
    hass: HomeAssistant,
    canary,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the creation and values of the sensors for Canary Pro."""
    online_device_at_home = mock_device(20, "Dining Room", True, "Canary Pro")

    instance = canary.return_value
    instance.get_locations.return_value = [
        mock_location(100, "Home", True, devices=[online_device_at_home]),
    ]

    instance.get_latest_readings.return_value = [
        mock_reading("temperature", "21.12"),
        mock_reading("humidity", "50.46"),
        mock_reading("air_quality", "0.59"),
    ]

    with patch("homeassistant.components.canary.PLATFORMS", ["sensor"]):
        await init_integration(hass)

    sensors = {
        "dining_room_home_dining_room_temperature": (
            "20_temperature",
            "21.12",
            UnitOfTemperature.CELSIUS,
            SensorDeviceClass.TEMPERATURE,
            None,
        ),
        "dining_room_home_dining_room_humidity": (
            "20_humidity",
            "50.46",
            PERCENTAGE,
            SensorDeviceClass.HUMIDITY,
            None,
        ),
        "dining_room_home_dining_room_air_quality": (
            "20_air_quality",
            "0.59",
            None,
            None,
            "mdi:weather-windy",
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
    assert device.model == "Canary Pro"