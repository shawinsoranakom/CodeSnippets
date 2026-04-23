async def test_core_climate_timer(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_asyncsleepiq
) -> None:
    """Test the SleepIQ core climate number values for a bed with two sides."""
    entry = await setup_platform(hass, NUMBER_DOMAIN)

    state = hass.states.get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_core_climate_timer"
    )
    assert state.state == "240.0"
    assert state.attributes.get(ATTR_ICON) == "mdi:timer"
    assert state.attributes.get(ATTR_MIN) == 0
    assert state.attributes.get(ATTR_MAX) == 600
    assert state.attributes.get(ATTR_STEP) == 30
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} {SLEEPER_L_NAME} Core Climate Timer"
    )

    entry = entity_registry.async_get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_core_climate_timer"
    )
    assert entry
    assert entry.unique_id == f"{BED_ID}_L_core_climate_timer"

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_core_climate_timer",
            ATTR_VALUE: 420,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    assert mock_asyncsleepiq.beds[BED_ID].foundation.core_climates[0].timer == 420