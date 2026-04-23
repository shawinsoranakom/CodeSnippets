async def test_state_change(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test if the state changes at next setting/rising."""
    now = datetime(2016, 6, 1, 8, 0, 0, tzinfo=dt_util.UTC)
    with freeze_time(now):
        await async_setup_component(hass, sun.DOMAIN, {sun.DOMAIN: {}})

    await hass.async_block_till_done()

    test_time = dt_util.parse_datetime(
        hass.states.get(entity.ENTITY_ID).attributes[entity.STATE_ATTR_NEXT_RISING]
    )
    assert test_time is not None

    assert hass.states.get(entity.ENTITY_ID).state == sun.STATE_BELOW_HORIZON

    patched_time = test_time + timedelta(seconds=5)
    with freeze_time(patched_time):
        async_fire_time_changed(hass, patched_time)
        await hass.async_block_till_done()

    assert hass.states.get(entity.ENTITY_ID).state == sun.STATE_ABOVE_HORIZON

    # Update core configuration
    with patch("homeassistant.helpers.condition.dt_util.utcnow", return_value=now):
        await hass.config.async_update(longitude=hass.config.longitude + 90)
        await hass.async_block_till_done()

    assert hass.states.get(entity.ENTITY_ID).state == sun.STATE_ABOVE_HORIZON

    # Test listeners are not duplicated after a core configuration change
    test_time = dt_util.parse_datetime(
        hass.states.get(entity.ENTITY_ID).attributes[entity.STATE_ATTR_NEXT_DUSK]
    )
    assert test_time is not None

    patched_time = test_time + timedelta(seconds=5)
    caplog.clear()
    with freeze_time(patched_time):
        async_fire_time_changed(hass, patched_time)
        await hass.async_block_till_done()
        await hass.async_block_till_done()

    assert caplog.text.count("sun phase_update") == 1
    # Called once by time listener, once from Sun.update_events
    assert caplog.text.count("sun position_update") == 2

    assert hass.states.get(entity.ENTITY_ID).state == sun.STATE_BELOW_HORIZON