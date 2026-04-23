async def test_foot_warmer_timer(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_asyncsleepiq
) -> None:
    """Test the SleepIQ foot warmer number values for a bed with two sides."""
    entry = await setup_platform(hass, NUMBER_DOMAIN)

    state = hass.states.get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_foot_warming_timer"
    )
    assert state.state == "120.0"
    assert state.attributes.get(ATTR_ICON) == "mdi:timer"
    assert state.attributes.get(ATTR_MIN) == 30
    assert state.attributes.get(ATTR_MAX) == 360
    assert state.attributes.get(ATTR_STEP) == 30
    assert (
        state.attributes.get(ATTR_FRIENDLY_NAME)
        == f"{BED_NAME} SleepNumber {BED_NAME} {SLEEPER_L_NAME} Foot Warming Timer"
    )

    entry = entity_registry.async_get(
        f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_foot_warming_timer"
    )
    assert entry
    assert entry.unique_id == f"{BED_ID}_L_foot_warming_timer"

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: f"number.{BED_NAME_LOWER}_sleepnumber_{BED_NAME_LOWER}_{SLEEPER_L_NAME_LOWER}_foot_warming_timer",
            ATTR_VALUE: 300,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    assert mock_asyncsleepiq.beds[BED_ID].foundation.foot_warmers[0].timer == 300