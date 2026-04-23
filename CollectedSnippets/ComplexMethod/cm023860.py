async def test_availability(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test entity configuration."""

    respx.get("http://localhost").respond(
        status_code=HTTPStatus.OK,
        json={"beer": 1},
    )
    assert await async_setup_component(
        hass,
        SWITCH_DOMAIN,
        {
            SWITCH_DOMAIN: {
                # REST configuration
                CONF_PLATFORM: DOMAIN,
                CONF_METHOD: "POST",
                CONF_RESOURCE: "http://localhost",
                # Entity configuration
                CONF_NAME: "{{'REST' + ' ' + 'Switch'}}",
                "is_on_template": "{{ value_json.beer == 1 }}",
                "availability": "{{ value_json.beer is defined }}",
                CONF_ICON: "mdi:{{ value_json.beer }}",
                CONF_PICTURE: "{{ value_json.beer }}.png",
            },
        },
    )
    await async_setup_component(hass, "homeassistant", {})
    await hass.async_block_till_done()

    state = hass.states.get("switch.rest_switch")
    assert state
    assert state.state == STATE_ON
    assert state.attributes["icon"] == "mdi:1"
    assert state.attributes["entity_picture"] == "1.png"

    respx.get("http://localhost").respond(
        status_code=HTTPStatus.OK,
        json={"x": 1},
    )
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: ["switch.rest_switch"]},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("switch.rest_switch")
    assert state
    assert state.state == STATE_UNAVAILABLE
    assert "icon" not in state.attributes
    assert "entity_picture" not in state.attributes

    respx.get("http://localhost").respond(
        status_code=HTTPStatus.OK,
        json={"beer": 0},
    )
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {ATTR_ENTITY_ID: ["switch.rest_switch"]},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("switch.rest_switch")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes["icon"] == "mdi:0"
    assert state.attributes["entity_picture"] == "0.png"