async def test_remote_sensor_ids_names(hass: HomeAssistant) -> None:
    """Test getting ids and names_by_user for thermostat."""
    await setup_platform(hass, [const.Platform.CLIMATE, const.Platform.SENSOR])
    platform = hass.data[const.Platform.CLIMATE].entities
    for entity in platform:
        if entity.entity_id == "climate.ecobee":
            thermostat = entity
            break

    assert thermostat is not None

    remote_sensor_ids_names = thermostat.remote_sensor_ids_names
    for id_name in remote_sensor_ids_names:
        assert id_name.get("id") is not None

    name_by_user_list = [item["name_by_user"] for item in remote_sensor_ids_names]
    assert sorted(name_by_user_list) == sorted(["Remote Sensor 1", "ecobee"])