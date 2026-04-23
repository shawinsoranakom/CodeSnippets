async def test_core_climate(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_asyncsleepiq: MagicMock,
) -> None:
    """Test the SleepIQ select entity for core climate."""
    entry = await setup_platform(hass, SELECT_DOMAIN)

    state = hass.states.get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_core_climate"
    )
    assert state.state == "cooling_medium"
    assert state.attributes.get(ATTR_ICON) == "mdi:heat-wave"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} {SLEEPER_L_NAME} Core Climate"
    )

    entry = entity_registry.async_get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_core_climate"
    )
    assert entry
    assert entry.unique_id == f"{SLEEPER_L_ID}_core_climate"

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_core_climate",
            ATTR_OPTION: "off",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_asyncsleepiq.beds[BED_ID].foundation.core_climates[
        0
    ].turn_off.assert_called_once()

    state = hass.states.get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_R_NAME_LOWER}_core_climate"
    )
    assert state.state == CoreTemps.OFF.name.lower()
    assert state.attributes.get(ATTR_ICON) == "mdi:heat-wave"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} {SLEEPER_R_NAME} Core Climate"
    )

    entry = entity_registry.async_get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_R_NAME_LOWER}_core_climate"
    )
    assert entry
    assert entry.unique_id == f"{SLEEPER_R_ID}_core_climate"

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_R_NAME_LOWER}_core_climate",
            ATTR_OPTION: "heating_high",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_asyncsleepiq.beds[BED_ID].foundation.core_climates[
        1
    ].turn_on.assert_called_once()
    mock_asyncsleepiq.beds[BED_ID].foundation.core_climates[
        1
    ].turn_on.assert_called_with(CoreTemps.HEATING_PUSH_HIGH, CORE_CLIMATE_TIME)