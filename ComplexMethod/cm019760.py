async def test_start_service(hass: HomeAssistant) -> None:
    """Test the start/stop service."""
    await async_setup_component(hass, DOMAIN, {DOMAIN: {"test1": {CONF_DURATION: 10}}})

    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_IDLE
    assert state.attributes == {
        ATTR_EDITABLE: False,
        ATTR_DURATION: "0:00:10",
    }

    await hass.services.async_call(
        DOMAIN, SERVICE_START, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_ACTIVE
    assert state.attributes == {
        ATTR_EDITABLE: False,
        ATTR_DURATION: "0:00:10",
        ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=10)).isoformat(),
        ATTR_REMAINING: "0:00:10",
    }

    await hass.services.async_call(
        DOMAIN, SERVICE_CANCEL, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_IDLE
    assert state.attributes == {
        ATTR_EDITABLE: False,
        ATTR_DURATION: "0:00:10",
    }

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CHANGE,
            {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: 10},
            blocking=True,
        )

    await hass.services.async_call(
        DOMAIN,
        SERVICE_START,
        {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: 15},
        blocking=True,
    )
    await hass.async_block_till_done()
    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_ACTIVE
    assert state.attributes == {
        ATTR_EDITABLE: False,
        ATTR_DURATION: "0:00:15",
        ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=15)).isoformat(),
        ATTR_REMAINING: "0:00:15",
    }

    with pytest.raises(
        HomeAssistantError,
        match="Not possible to change timer timer.test1 beyond duration",
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CHANGE,
            {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: 20},
            blocking=True,
        )

    with pytest.raises(
        HomeAssistantError,
        match="Not possible to change timer timer.test1 to negative time remaining",
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CHANGE,
            {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: -20},
            blocking=True,
        )

    await hass.services.async_call(
        DOMAIN,
        SERVICE_CHANGE,
        {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: -3},
        blocking=True,
    )
    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_ACTIVE
    assert state.attributes == {
        ATTR_EDITABLE: False,
        ATTR_DURATION: "0:00:15",
        ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=12)).isoformat(),
        ATTR_REMAINING: "0:00:12",
    }

    await hass.services.async_call(
        DOMAIN,
        SERVICE_CHANGE,
        {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: 2},
        blocking=True,
    )
    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_ACTIVE
    assert state.attributes == {
        ATTR_EDITABLE: False,
        ATTR_DURATION: "0:00:15",
        ATTR_FINISHES_AT: (utcnow() + timedelta(seconds=14)).isoformat(),
        ATTR_REMAINING: "0:00:14",
    }

    await hass.services.async_call(
        DOMAIN, SERVICE_CANCEL, {CONF_ENTITY_ID: "timer.test1"}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_IDLE
    assert state.attributes == {
        ATTR_EDITABLE: False,
        ATTR_DURATION: "0:00:10",
    }

    with pytest.raises(
        HomeAssistantError,
        match="Timer timer.test1 is not running, only active timers can be changed",
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_CHANGE,
            {CONF_ENTITY_ID: "timer.test1", CONF_DURATION: 2},
            blocking=True,
        )

    state = hass.states.get("timer.test1")
    assert state
    assert state.state == STATUS_IDLE
    assert state.attributes == {
        ATTR_EDITABLE: False,
        ATTR_DURATION: "0:00:10",
    }