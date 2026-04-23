async def test_plant_group(hass: HomeAssistant) -> None:
    """Test plant states can be grouped."""

    entity_ids = [
        "plant.upstairs",
        "plant.downstairs",
    ]

    assert await async_setup_component(
        hass,
        "plant",
        {
            "plant": {
                "plantname": {
                    "sensors": {
                        "moisture": "sensor.mqtt_plant_moisture",
                        "battery": "sensor.mqtt_plant_battery",
                        "temperature": "sensor.mqtt_plant_temperature",
                        "conductivity": "sensor.mqtt_plant_conductivity",
                        "brightness": "sensor.mqtt_plant_brightness",
                    },
                    "min_moisture": 20,
                    "max_moisture": 60,
                    "min_battery": 17,
                    "min_conductivity": 500,
                    "min_temperature": 15,
                    "min_brightness": 500,
                }
            }
        },
    )
    assert await async_setup_component(
        hass,
        "group",
        {
            "group": {
                "plants": {"entities": entity_ids},
                "plant_with_binary_sensors": {
                    "entities": [*entity_ids, "binary_sensor.planter"]
                },
            }
        },
    )
    await hass.async_block_till_done()

    hass.states.async_set("binary_sensor.planter", "off")
    for entity_id in entity_ids:
        hass.states.async_set(entity_id, "ok")
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert hass.states.get("group.plants").state == "ok"
    assert hass.states.get("group.plant_with_binary_sensors").state == "off"

    hass.states.async_set("binary_sensor.planter", "on")
    for entity_id in entity_ids:
        hass.states.async_set(entity_id, "problem")

    await hass.async_block_till_done()
    assert hass.states.get("group.plants").state == "problem"
    assert hass.states.get("group.plant_with_binary_sensors").state == "on"