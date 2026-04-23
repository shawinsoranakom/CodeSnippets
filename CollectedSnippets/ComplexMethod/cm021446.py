async def test_methods(hass: HomeAssistant) -> None:
    """Test if methods call the services as expected."""
    await common.async_start(hass, ENTITY_VACUUM_BASIC)
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_VACUUM_BASIC)
    assert state.state == VacuumActivity.CLEANING

    await common.async_stop(hass, ENTITY_VACUUM_BASIC)
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_VACUUM_BASIC)
    assert state.state == VacuumActivity.IDLE

    state = hass.states.get(ENTITY_VACUUM_COMPLETE)
    await hass.async_block_till_done()
    assert state.state == VacuumActivity.DOCKED

    await async_setup_component(hass, "notify", {})
    await hass.async_block_till_done()
    await common.async_locate(hass, ENTITY_VACUUM_COMPLETE)
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_VACUUM_COMPLETE)
    assert state.state == VacuumActivity.IDLE

    await common.async_return_to_base(hass, ENTITY_VACUUM_COMPLETE)
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_VACUUM_COMPLETE)
    assert state.state == VacuumActivity.RETURNING

    await common.async_set_fan_speed(
        hass, FAN_SPEEDS[-1], entity_id=ENTITY_VACUUM_COMPLETE
    )
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_VACUUM_COMPLETE)
    assert state.attributes.get(ATTR_FAN_SPEED) == FAN_SPEEDS[-1]

    await common.async_clean_spot(hass, ENTITY_VACUUM_COMPLETE)
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_VACUUM_COMPLETE)
    assert state.state == VacuumActivity.CLEANING

    await common.async_pause(hass, ENTITY_VACUUM_COMPLETE)
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_VACUUM_COMPLETE)
    assert state.state == VacuumActivity.PAUSED

    await common.async_return_to_base(hass, ENTITY_VACUUM_COMPLETE)
    state = hass.states.get(ENTITY_VACUUM_COMPLETE)
    assert state.state == VacuumActivity.RETURNING

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_VACUUM_COMPLETE)
    assert state.state == VacuumActivity.DOCKED