async def test_firmness(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_asyncsleepiq
) -> None:
    """Test the SleepIQ firmness number values for a bed with two sides."""
    entry = await setup_platform(hass, NUMBER_DOMAIN)

    state = hass.states.get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_firmness"
    )
    assert state.state == "40.0"
    assert state.attributes.get(ATTR_ICON) == "mdi:bed"
    assert state.attributes.get(ATTR_MIN) == 5
    assert state.attributes.get(ATTR_MAX) == 100
    assert state.attributes.get(ATTR_STEP) == 5
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} {SLEEPER_L_NAME} Firmness"
    )

    entry = entity_registry.async_get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_firmness"
    )
    assert entry
    assert entry.unique_id == f"{SLEEPER_L_ID}_firmness"

    state = hass.states.get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_R_NAME_LOWER}_firmness"
    )
    assert state.state == "80.0"
    assert state.attributes.get(ATTR_ICON) == "mdi:bed"
    assert state.attributes.get(ATTR_MIN) == 5
    assert state.attributes.get(ATTR_MAX) == 100
    assert state.attributes.get(ATTR_STEP) == 5
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} {SLEEPER_R_NAME} Firmness"
    )

    entry = entity_registry.async_get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_R_NAME_LOWER}_firmness"
    )
    assert entry
    assert entry.unique_id == f"{SLEEPER_R_ID}_firmness"

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_firmness",
            ATTR_VALUE: 42,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_asyncsleepiq.beds[BED_ID].sleepers[0].set_sleepnumber.assert_called_once()
    mock_asyncsleepiq.beds[BED_ID].sleepers[0].set_sleepnumber.assert_called_with(42)