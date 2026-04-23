async def test_is_opening_closing(hass: HomeAssistant) -> None:
    """Test is_opening property."""
    await hass.services.async_call(
        VALVE_DOMAIN, SERVICE_OPEN_VALVE, {ATTR_ENTITY_ID: VALVE_GROUP}, blocking=True
    )
    await hass.async_block_till_done()

    # Both valves opening -> opening
    assert hass.states.get(DEMO_VALVE_POS1).state == ValveState.OPENING
    assert hass.states.get(DEMO_VALVE_POS2).state == ValveState.OPENING
    assert hass.states.get(VALVE_GROUP).state == ValveState.OPENING

    for _ in range(10):
        future = dt_util.utcnow() + timedelta(seconds=1)
        async_fire_time_changed(hass, future)
        await hass.async_block_till_done()

    await hass.services.async_call(
        VALVE_DOMAIN, SERVICE_CLOSE_VALVE, {ATTR_ENTITY_ID: VALVE_GROUP}, blocking=True
    )

    # Both valves closing -> closing
    assert hass.states.get(DEMO_VALVE_POS1).state == ValveState.CLOSING
    assert hass.states.get(DEMO_VALVE_POS2).state == ValveState.CLOSING
    assert hass.states.get(VALVE_GROUP).state == ValveState.CLOSING

    hass.states.async_set(
        DEMO_VALVE_POS1, ValveState.OPENING, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()

    # Closing + Opening -> Opening
    assert hass.states.get(DEMO_VALVE_POS2).state == ValveState.CLOSING
    assert hass.states.get(DEMO_VALVE_POS1).state == ValveState.OPENING
    assert hass.states.get(VALVE_GROUP).state == ValveState.OPENING

    hass.states.async_set(
        DEMO_VALVE_POS1, ValveState.CLOSING, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()

    # Both valves closing -> closing
    assert hass.states.get(DEMO_VALVE_POS2).state == ValveState.CLOSING
    assert hass.states.get(DEMO_VALVE_POS1).state == ValveState.CLOSING
    assert hass.states.get(VALVE_GROUP).state == ValveState.CLOSING

    # Closed + Closing -> Closing
    hass.states.async_set(
        DEMO_VALVE_POS1, ValveState.CLOSED, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()
    assert hass.states.get(DEMO_VALVE_POS2).state == ValveState.CLOSING
    assert hass.states.get(DEMO_VALVE_POS1).state == ValveState.CLOSED
    assert hass.states.get(VALVE_GROUP).state == ValveState.CLOSING

    # Open + Closing -> Closing
    hass.states.async_set(
        DEMO_VALVE_POS1, ValveState.OPEN, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()
    assert hass.states.get(DEMO_VALVE_POS2).state == ValveState.CLOSING
    assert hass.states.get(DEMO_VALVE_POS1).state == ValveState.OPEN
    assert hass.states.get(VALVE_GROUP).state == ValveState.CLOSING

    # Closed + Opening -> Closing
    hass.states.async_set(
        DEMO_VALVE_POS2, ValveState.OPENING, {ATTR_SUPPORTED_FEATURES: 11}
    )
    hass.states.async_set(
        DEMO_VALVE_POS1, ValveState.CLOSED, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()
    assert hass.states.get(DEMO_VALVE_POS2).state == ValveState.OPENING
    assert hass.states.get(DEMO_VALVE_POS1).state == ValveState.CLOSED
    assert hass.states.get(VALVE_GROUP).state == ValveState.OPENING

    # Open + Opening -> Closing
    hass.states.async_set(
        DEMO_VALVE_POS1, ValveState.OPEN, {ATTR_SUPPORTED_FEATURES: 11}
    )
    await hass.async_block_till_done()
    assert hass.states.get(DEMO_VALVE_POS2).state == ValveState.OPENING
    assert hass.states.get(DEMO_VALVE_POS1).state == ValveState.OPEN
    assert hass.states.get(VALVE_GROUP).state == ValveState.OPENING