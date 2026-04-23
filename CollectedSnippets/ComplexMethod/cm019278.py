async def test_state_reporting_any(hass: HomeAssistant) -> None:
    """Test the state reporting in 'any' mode.

    The group state is unavailable if all group members are unavailable.
    Otherwise, the group state is unknown if all group members are unknown.
    Otherwise, the group state is on if at least one group member is on.
    Otherwise, the group state is off.
    """
    await async_setup_component(
        hass,
        LIGHT_DOMAIN,
        {
            LIGHT_DOMAIN: {
                "platform": DOMAIN,
                "entities": ["light.test1", "light.test2"],
                "all": "false",
            }
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    # Initial state with no group member in the state machine -> unavailable
    assert hass.states.get("light.light_group").state == STATE_UNAVAILABLE

    # All group members unavailable -> unavailable
    hass.states.async_set("light.test1", STATE_UNAVAILABLE)
    hass.states.async_set("light.test2", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get("light.light_group").state == STATE_UNAVAILABLE

    # All group members unknown -> unknown
    hass.states.async_set("light.test1", STATE_UNKNOWN)
    hass.states.async_set("light.test2", STATE_UNKNOWN)
    await hass.async_block_till_done()
    assert hass.states.get("light.light_group").state == STATE_UNKNOWN

    # Group members unknown or unavailable -> unknown
    hass.states.async_set("light.test1", STATE_UNKNOWN)
    hass.states.async_set("light.test2", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get("light.light_group").state == STATE_UNKNOWN

    # At least one member on -> group on
    hass.states.async_set("light.test1", STATE_ON)
    hass.states.async_set("light.test2", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get("light.light_group").state == STATE_ON

    hass.states.async_set("light.test1", STATE_ON)
    hass.states.async_set("light.test2", STATE_OFF)
    await hass.async_block_till_done()
    assert hass.states.get("light.light_group").state == STATE_ON

    hass.states.async_set("light.test1", STATE_ON)
    hass.states.async_set("light.test2", STATE_ON)
    await hass.async_block_till_done()
    assert hass.states.get("light.light_group").state == STATE_ON

    hass.states.async_set("light.test1", STATE_ON)
    hass.states.async_set("light.test2", STATE_UNKNOWN)
    await hass.async_block_till_done()
    assert hass.states.get("light.light_group").state == STATE_ON

    # Otherwise -> off
    hass.states.async_set("light.test1", STATE_OFF)
    hass.states.async_set("light.test2", STATE_OFF)
    await hass.async_block_till_done()
    assert hass.states.get("light.light_group").state == STATE_OFF

    hass.states.async_set("light.test1", STATE_UNKNOWN)
    hass.states.async_set("light.test2", STATE_OFF)
    await hass.async_block_till_done()
    assert hass.states.get("light.light_group").state == STATE_OFF

    hass.states.async_set("light.test1", STATE_UNAVAILABLE)
    hass.states.async_set("light.test2", STATE_OFF)
    await hass.async_block_till_done()
    assert hass.states.get("light.light_group").state == STATE_OFF

    # All group members removed from the state machine -> unavailable
    hass.states.async_remove("light.test1")
    hass.states.async_remove("light.test2")
    await hass.async_block_till_done()
    assert hass.states.get("light.light_group").state == STATE_UNAVAILABLE