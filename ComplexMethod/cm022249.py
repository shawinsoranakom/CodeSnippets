async def test_sensor_reauth_trigger(
    hass: HomeAssistant, setup_integration: ComponentSetup
) -> None:
    """Test reauth is triggered after a refresh error."""
    mock = await setup_integration()

    state = hass.states.get("sensor.google_for_developers_latest_upload")
    assert state.state == "What's new in Google Home in less than 1 minute"

    state = hass.states.get("sensor.google_for_developers_subscribers")
    assert state.state == "2290000"

    state = hass.states.get("sensor.google_for_developers_views")
    assert state.state == "214141263"

    mock.set_thrown_exception(UnauthorizedError())
    future = dt_util.utcnow() + timedelta(minutes=15)
    async_fire_time_changed(hass, future)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()

    assert len(flows) == 1
    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN
    assert flow["context"]["source"] == config_entries.SOURCE_REAUTH