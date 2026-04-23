async def test_services_filter_parameters(
    hass: HomeAssistant,
    mock_light_profiles,
    mock_light_entities: list[MockLight],
) -> None:
    """Test turn_on and turn_off filters unsupported parameters."""
    setup_test_component_platform(hass, light.DOMAIN, mock_light_entities)

    assert await async_setup_component(
        hass, light.DOMAIN, {light.DOMAIN: {CONF_PLATFORM: "test"}}
    )
    await hass.async_block_till_done()

    ent1, _, _ = mock_light_entities

    # turn off the light by setting brightness to 0, this should work even if the light
    # doesn't support brightness
    await hass.services.async_call(
        light.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_MATCH_ALL}, blocking=True
    )
    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL, light.ATTR_BRIGHTNESS: 0},
        blocking=True,
    )

    assert not light.is_on(hass, ent1.entity_id)

    # Ensure all unsupported attributes are filtered when light is turned on
    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ent1.entity_id,
            light.ATTR_BRIGHTNESS: 0,
            light.ATTR_EFFECT: "fun_effect",
            light.ATTR_FLASH: "short",
            light.ATTR_TRANSITION: 10,
        },
        blocking=True,
    )
    _, data = ent1.last_call("turn_on")
    assert data == {}

    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ent1.entity_id,
            light.ATTR_COLOR_TEMP_KELVIN: 6535,
        },
        blocking=True,
    )
    _, data = ent1.last_call("turn_on")
    assert data == {}

    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ent1.entity_id,
            light.ATTR_HS_COLOR: (0, 0),
        },
        blocking=True,
    )
    _, data = ent1.last_call("turn_on")
    assert data == {}

    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ent1.entity_id,
            light.ATTR_RGB_COLOR: (0, 0, 0),
        },
        blocking=True,
    )
    _, data = ent1.last_call("turn_on")
    assert data == {}

    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ent1.entity_id,
            light.ATTR_RGBW_COLOR: (0, 0, 0, 0),
        },
        blocking=True,
    )
    _, data = ent1.last_call("turn_on")
    assert data == {}

    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ent1.entity_id,
            light.ATTR_RGBWW_COLOR: (0, 0, 0, 0, 0),
        },
        blocking=True,
    )
    _, data = ent1.last_call("turn_on")
    assert data == {}

    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ent1.entity_id,
            light.ATTR_XY_COLOR: (0, 0),
        },
        blocking=True,
    )
    _, data = ent1.last_call("turn_on")
    assert data == {}

    # Ensure all unsupported attributes are filtered when light is turned off
    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ent1.entity_id,
            light.ATTR_BRIGHTNESS: 0,
            light.ATTR_EFFECT: "fun_effect",
            light.ATTR_FLASH: "short",
            light.ATTR_TRANSITION: 10,
        },
        blocking=True,
    )

    assert not light.is_on(hass, ent1.entity_id)

    _, data = ent1.last_call("turn_off")
    assert data == {}

    await hass.services.async_call(
        light.DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: ent1.entity_id,
            light.ATTR_FLASH: "short",
            light.ATTR_TRANSITION: 10,
        },
        blocking=True,
    )

    assert not light.is_on(hass, ent1.entity_id)

    _, data = ent1.last_call("turn_off")
    assert data == {}