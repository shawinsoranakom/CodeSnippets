async def test_templates_with_yaml(
    recorder_mock: Recorder, hass: HomeAssistant
) -> None:
    """Test the SQL sensor from yaml config with templates."""

    hass.states.async_set("sensor.input1", "on")
    hass.states.async_set("sensor.input2", "on")
    await hass.async_block_till_done()

    assert await async_setup_component(hass, DOMAIN, YAML_CONFIG_ALL_TEMPLATES)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.get_values_with_template")
    assert state.state == "5"
    assert state.attributes[CONF_ICON] == "mdi:on"
    assert state.attributes["entity_picture"] == "/local/picture1.jpg"

    hass.states.async_set("sensor.input1", "off")
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(minutes=1),
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("sensor.get_values_with_template")
    assert state.state == "5"
    assert state.attributes[CONF_ICON] == "mdi:off"
    assert state.attributes["entity_picture"] == "/local/picture2.jpg"

    hass.states.async_set("sensor.input2", "off")
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(minutes=2),
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("sensor.get_values_with_template")
    assert state.state == STATE_UNAVAILABLE
    assert CONF_ICON not in state.attributes
    assert "entity_picture" not in state.attributes

    hass.states.async_set("sensor.input1", "on")
    hass.states.async_set("sensor.input2", "on")
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(minutes=3),
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("sensor.get_values_with_template")
    assert state.state == "5"
    assert state.attributes[CONF_ICON] == "mdi:on"
    assert state.attributes["entity_picture"] == "/local/picture1.jpg"