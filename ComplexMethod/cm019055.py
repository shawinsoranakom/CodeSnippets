async def test_foot_warmer(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_asyncsleepiq: MagicMock,
) -> None:
    """Test the SleepIQ select entity for foot warmers."""
    entry = await setup_platform(hass, SELECT_DOMAIN)

    state = hass.states.get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_foot_warmer"
    )
    assert state.state == FootWarmingTemps.MEDIUM.name.lower()
    assert state.attributes.get(ATTR_ICON) == "mdi:heat-wave"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} {SLEEPER_L_NAME} Foot Warmer"
    )

    entry = entity_registry.async_get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_foot_warmer"
    )
    assert entry
    assert entry.unique_id == f"{SLEEPER_L_ID}_foot_warmer"

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_foot_warmer",
            ATTR_OPTION: "off",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_asyncsleepiq.beds[BED_ID].foundation.foot_warmers[
        0
    ].turn_off.assert_called_once()

    state = hass.states.get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_R_NAME_LOWER}_foot_warmer"
    )
    assert state.state == FootWarmingTemps.OFF.name.lower()
    assert state.attributes.get(ATTR_ICON) == "mdi:heat-wave"
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} {SLEEPER_R_NAME} Foot Warmer"
    )

    entry = entity_registry.async_get(
        f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_R_NAME_LOWER}_foot_warmer"
    )
    assert entry
    assert entry.unique_id == f"{SLEEPER_R_ID}_foot_warmer"

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: f"select.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_R_NAME_LOWER}_foot_warmer",
            ATTR_OPTION: "high",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_asyncsleepiq.beds[BED_ID].foundation.foot_warmers[
        1
    ].turn_on.assert_called_once()
    mock_asyncsleepiq.beds[BED_ID].foundation.foot_warmers[
        1
    ].turn_on.assert_called_with(FootWarmingTemps.HIGH, FOOT_WARM_TIME)