async def test_templates_with_yaml(hass: HomeAssistant) -> None:
    """Test the Scrape sensor from yaml config with templates."""

    hass.states.async_set("sensor.input1", "on")
    hass.states.async_set("sensor.input2", "on")
    await hass.async_block_till_done()

    config = {
        DOMAIN: [
            return_integration_config(
                sensors=[
                    {
                        CONF_NAME: "Get values with template",
                        CONF_SELECT: ".current-version h1",
                        CONF_INDEX: 0,
                        CONF_UNIQUE_ID: "3699ef88-69e6-11ed-a1eb-0242ac120002",
                        CONF_ICON: '{% if states("sensor.input1")=="on" %} mdi:on {% else %} mdi:off {% endif %}',
                        CONF_PICTURE: '{% if states("sensor.input1")=="on" %} /local/picture1.jpg {% else %} /local/picture2.jpg {% endif %}',
                        CONF_AVAILABILITY: '{{ states("sensor.input2")=="on" }}',
                    }
                ]
            )
        ]
    }

    mocker = MockRestData("test_scrape_sensor")
    with patch(
        "homeassistant.components.rest.RestData",
        return_value=mocker,
    ):
        assert await async_setup_component(hass, DOMAIN, config)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.get_values_with_template")
    assert state.state == "Current Version: 2021.12.10"
    assert state.attributes[CONF_ICON] == "mdi:on"
    assert state.attributes["entity_picture"] == "/local/picture1.jpg"

    hass.states.async_set("sensor.input1", "off")
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(minutes=10),
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("sensor.get_values_with_template")
    assert state.state == "Current Version: 2021.12.10"
    assert state.attributes[CONF_ICON] == "mdi:off"
    assert state.attributes["entity_picture"] == "/local/picture2.jpg"

    hass.states.async_set("sensor.input2", "off")
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(minutes=20),
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("sensor.get_values_with_template")
    assert state.state == STATE_UNAVAILABLE

    hass.states.async_set("sensor.input1", "on")
    hass.states.async_set("sensor.input2", "on")
    await hass.async_block_till_done()

    async_fire_time_changed(
        hass,
        dt_util.utcnow() + timedelta(minutes=30),
    )
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("sensor.get_values_with_template")
    assert state.state == "Current Version: 2021.12.10"
    assert state.attributes[CONF_ICON] == "mdi:on"
    assert state.attributes["entity_picture"] == "/local/picture1.jpg"