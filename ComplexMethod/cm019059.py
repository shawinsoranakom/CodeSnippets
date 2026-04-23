async def test_actuators(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_asyncsleepiq
) -> None:
    """Test the SleepIQ actuator position values for a bed with adjustable head and foot."""
    entry = await setup_platform(hass, NUMBER_DOMAIN)

    state = hass.states.get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_right_head_position"
    )
    assert state.state == "60.0"
    assert state.attributes.get(ATTR_ICON) == "mdi:bed"
    assert state.attributes.get(ATTR_MIN) == 0
    assert state.attributes.get(ATTR_MAX) == 100
    assert state.attributes.get(ATTR_STEP) == 1
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} Right Head Position"
    )

    entry = entity_registry.async_get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_right_head_position"
    )
    assert entry
    assert entry.unique_id == f"{BED_ID}_R_H"

    state = hass.states.get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_left_head_position"
    )
    assert state.state == "50.0"
    assert state.attributes.get(ATTR_ICON) == "mdi:bed"
    assert state.attributes.get(ATTR_MIN) == 0
    assert state.attributes.get(ATTR_MAX) == 100
    assert state.attributes.get(ATTR_STEP) == 1
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} Left Head Position"
    )

    entry = entity_registry.async_get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_left_head_position"
    )
    assert entry
    assert entry.unique_id == f"{BED_ID}_L_H"

    state = hass.states.get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_foot_position"
    )
    assert state.state == "10.0"
    assert state.attributes.get(ATTR_ICON) == "mdi:bed"
    assert state.attributes.get(ATTR_MIN) == 0
    assert state.attributes.get(ATTR_MAX) == 100
    assert state.attributes.get(ATTR_STEP) == 1
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} Foot Position"
    )

    entry = entity_registry.async_get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_foot_position"
    )
    assert entry
    assert entry.unique_id == f"{BED_ID}_F"

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_right_head_position",
            ATTR_VALUE: 42,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_asyncsleepiq.beds[BED_ID].foundation.actuators[
        0
    ].set_position.assert_called_once()
    mock_asyncsleepiq.beds[BED_ID].foundation.actuators[
        0
    ].set_position.assert_called_with(42)