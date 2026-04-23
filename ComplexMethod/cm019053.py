async def test_binary_sensors(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_asyncsleepiq
) -> None:
    """Test the SleepIQ binary sensors."""
    await setup_platform(hass, BINARY_SENSOR_DOMAIN)

    state = hass.states.get(
        f"binary_sensor.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_is_in_bed"
    )
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ICON) == "mdi:bed"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == BinarySensorDeviceClass.OCCUPANCY
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} {SLEEPER_L_NAME} Is In Bed"
    )

    entity = entity_registry.async_get(
        f"binary_sensor.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_is_in_bed"
    )
    assert entity
    assert entity.unique_id == f"{SLEEPER_L_ID}_is_in_bed"

    state = hass.states.get(
        f"binary_sensor.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_R_NAME_LOWER}_is_in_bed"
    )
    assert state.state == STATE_OFF
    assert state.attributes.get(ATTR_ICON) == "mdi:bed-empty"
    assert state.attributes.get(ATTR_DEVICE_CLASS) == BinarySensorDeviceClass.OCCUPANCY
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} {SLEEPER_R_NAME} Is In Bed"
    )

    entity = entity_registry.async_get(
        f"binary_sensor.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_R_NAME_LOWER}_is_in_bed"
    )
    assert entity
    assert entity.unique_id == f"{SLEEPER_R_ID}_is_in_bed"