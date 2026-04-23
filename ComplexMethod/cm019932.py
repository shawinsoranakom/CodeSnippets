async def test_methods(hass: HomeAssistant) -> None:
    """Test if methods call the services as expected."""
    # Test is_on
    hass.states.async_set("light.test", STATE_ON)
    assert light.is_on(hass, "light.test")

    hass.states.async_set("light.test", STATE_OFF)
    assert not light.is_on(hass, "light.test")

    # Test turn_on
    turn_on_calls = async_mock_service(hass, light.DOMAIN, SERVICE_TURN_ON)

    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "entity_id_val",
            light.ATTR_TRANSITION: "transition_val",
            light.ATTR_BRIGHTNESS: "brightness_val",
            light.ATTR_RGB_COLOR: "rgb_color_val",
            light.ATTR_XY_COLOR: "xy_color_val",
            light.ATTR_PROFILE: "profile_val",
            light.ATTR_COLOR_NAME: "color_name_val",
        },
        blocking=True,
    )

    assert len(turn_on_calls) == 1
    call = turn_on_calls[-1]

    assert call.domain == light.DOMAIN
    assert call.service == SERVICE_TURN_ON
    assert call.data.get(ATTR_ENTITY_ID) == "entity_id_val"
    assert call.data.get(light.ATTR_TRANSITION) == "transition_val"
    assert call.data.get(light.ATTR_BRIGHTNESS) == "brightness_val"
    assert call.data.get(light.ATTR_RGB_COLOR) == "rgb_color_val"
    assert call.data.get(light.ATTR_XY_COLOR) == "xy_color_val"
    assert call.data.get(light.ATTR_PROFILE) == "profile_val"
    assert call.data.get(light.ATTR_COLOR_NAME) == "color_name_val"

    # Test turn_off
    turn_off_calls = async_mock_service(hass, light.DOMAIN, SERVICE_TURN_OFF)

    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: "entity_id_val",
            light.ATTR_TRANSITION: "transition_val",
        },
        blocking=True,
    )

    assert len(turn_off_calls) == 1
    call = turn_off_calls[-1]

    assert call.domain == light.DOMAIN
    assert call.service == SERVICE_TURN_OFF
    assert call.data[ATTR_ENTITY_ID] == "entity_id_val"
    assert call.data[light.ATTR_TRANSITION] == "transition_val"

    # Test toggle
    toggle_calls = async_mock_service(hass, light.DOMAIN, SERVICE_TOGGLE)

    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: "entity_id_val", light.ATTR_TRANSITION: "transition_val"},
        blocking=True,
    )

    assert len(toggle_calls) == 1
    call = toggle_calls[-1]

    assert call.domain == light.DOMAIN
    assert call.service == SERVICE_TOGGLE
    assert call.data[ATTR_ENTITY_ID] == "entity_id_val"
    assert call.data[light.ATTR_TRANSITION] == "transition_val"