async def test_state_reporting(hass: HomeAssistant) -> None:
    """Test the state reporting in 'any' mode.

    The group state is unavailable if all group members are unavailable.
    Otherwise, the group state is unknown if all group members are unknown.
    Otherwise, the group state is on if at least one group member is on.
    Otherwise, the group state is off.
    """
    await async_setup_component(
        hass,
        SWITCH_DOMAIN,
        {
            SWITCH_DOMAIN: {
                "platform": DOMAIN,
                "entities": ["switch.test1", "switch.test2"],
                "all": "false",
            }
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    # Initial state with no group member in the state machine -> unavailable
    assert hass.states.get("switch.switch_group").state == STATE_UNAVAILABLE

    # All group members unavailable -> unavailable
    hass.states.async_set("switch.test1", STATE_UNAVAILABLE)
    hass.states.async_set("switch.test2", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get("switch.switch_group").state == STATE_UNAVAILABLE

    # All group members unknown -> unknown
    hass.states.async_set("switch.test1", STATE_UNKNOWN)
    hass.states.async_set("switch.test2", STATE_UNKNOWN)
    await hass.async_block_till_done()
    assert hass.states.get("switch.switch_group").state == STATE_UNKNOWN

    # Group members unknown or unavailable -> unknown
    hass.states.async_set("switch.test1", STATE_UNKNOWN)
    hass.states.async_set("switch.test2", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get("switch.switch_group").state == STATE_UNKNOWN

    # At least one member on -> group on
    hass.states.async_set("switch.test1", STATE_ON)
    hass.states.async_set("switch.test2", STATE_UNAVAILABLE)
    await hass.async_block_till_done()
    assert hass.states.get("switch.switch_group").state == STATE_ON

    hass.states.async_set("switch.test1", STATE_ON)
    hass.states.async_set("switch.test2", STATE_OFF)
    await hass.async_block_till_done()
    assert hass.states.get("switch.switch_group").state == STATE_ON

    hass.states.async_set("switch.test1", STATE_ON)
    hass.states.async_set("switch.test2", STATE_ON)
    await hass.async_block_till_done()
    assert hass.states.get("switch.switch_group").state == STATE_ON

    hass.states.async_set("switch.test1", STATE_ON)
    hass.states.async_set("switch.test2", STATE_UNKNOWN)
    await hass.async_block_till_done()
    assert hass.states.get("switch.switch_group").state == STATE_ON

    # Otherwise -> off
    hass.states.async_set("switch.test1", STATE_OFF)
    hass.states.async_set("switch.test2", STATE_OFF)
    await hass.async_block_till_done()
    assert hass.states.get("switch.switch_group").state == STATE_OFF

    hass.states.async_set("switch.test1", STATE_UNKNOWN)
    hass.states.async_set("switch.test2", STATE_OFF)
    await hass.async_block_till_done()
    assert hass.states.get("switch.switch_group").state == STATE_OFF

    hass.states.async_set("switch.test1", STATE_UNAVAILABLE)
    hass.states.async_set("switch.test2", STATE_OFF)
    await hass.async_block_till_done()
    assert hass.states.get("switch.switch_group").state == STATE_OFF

    # All group members removed from the state machine -> unavailable
    hass.states.async_remove("switch.test1")
    hass.states.async_remove("switch.test2")
    await hass.async_block_till_done()
    assert hass.states.get("switch.switch_group").state == STATE_UNAVAILABLE