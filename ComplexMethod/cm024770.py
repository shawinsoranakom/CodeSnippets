async def test_state_already_set_avoid_ratelimit(hass: HomeAssistant) -> None:
    """Ensure we suppress state changes that will increase the rate limit when there is no change."""
    mocked_bulb = _mocked_bulb()
    properties = {**PROPERTIES}
    properties.pop("active_mode")
    properties.pop("nl_br")
    properties["color_mode"] = "3"  # HSV
    mocked_bulb.last_properties = properties
    mocked_bulb.bulb_type = BulbType.Color
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={**CONFIG_ENTRY_DATA, CONF_NIGHTLIGHT_SWITCH: False}
    )
    config_entry.add_to_hass(hass)
    with (
        _patch_discovery(),
        _patch_discovery_interval(),
        patch(f"{MODULE}.AsyncBulb", return_value=mocked_bulb),
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        # We use asyncio.create_task now to avoid
        # blocking starting so we need to block again
        await hass.async_block_till_done()

    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_HS_COLOR: (PROPERTIES["hue"], PROPERTIES["sat"]),
        },
        blocking=True,
    )
    assert mocked_bulb.async_set_hsv.mock_calls == []
    assert mocked_bulb.async_set_rgb.mock_calls == []
    assert mocked_bulb.async_set_color_temp.mock_calls == []
    assert mocked_bulb.async_set_brightness.mock_calls == []

    mocked_bulb.last_properties["color_mode"] = 1
    rgb = int(PROPERTIES["rgb"])
    blue = rgb & 0xFF
    green = (rgb >> 8) & 0xFF
    red = (rgb >> 16) & 0xFF

    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_RGB_COLOR: (red, green, blue)},
        blocking=True,
    )
    assert mocked_bulb.async_set_hsv.mock_calls == []
    assert mocked_bulb.async_set_rgb.mock_calls == []
    assert mocked_bulb.async_set_color_temp.mock_calls == []
    assert mocked_bulb.async_set_brightness.mock_calls == []
    mocked_bulb.async_set_rgb.reset_mock()

    mocked_bulb.last_properties["flowing"] = "1"
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_RGB_COLOR: (red, green, blue)},
        blocking=True,
    )
    assert mocked_bulb.async_set_hsv.mock_calls == []
    assert mocked_bulb.async_set_rgb.mock_calls == [
        call(255, 0, 0, duration=350, light_type=ANY)
    ]
    assert mocked_bulb.async_set_color_temp.mock_calls == []
    assert mocked_bulb.async_set_brightness.mock_calls == []
    mocked_bulb.async_set_rgb.reset_mock()
    mocked_bulb.last_properties["flowing"] = "0"

    # color model needs a workaround (see MODELS_WITH_DELAYED_ON_TRANSITION)
    mocked_bulb.model = "color"
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_BRIGHTNESS_PCT: PROPERTIES["bright"],
        },
        blocking=True,
    )
    assert mocked_bulb.async_set_hsv.mock_calls == []
    assert mocked_bulb.async_set_rgb.mock_calls == []
    assert mocked_bulb.async_set_color_temp.mock_calls == []
    assert mocked_bulb.async_set_brightness.mock_calls == [
        call(pytest.approx(50.1, 0.1), duration=350, light_type=ANY)
    ]
    mocked_bulb.async_set_brightness.reset_mock()

    mocked_bulb.model = "colora"  # colora does not need a workaround
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_LIGHT,
            ATTR_BRIGHTNESS_PCT: PROPERTIES["bright"],
        },
        blocking=True,
    )
    assert mocked_bulb.async_set_hsv.mock_calls == []
    assert mocked_bulb.async_set_rgb.mock_calls == []
    assert mocked_bulb.async_set_color_temp.mock_calls == []
    assert mocked_bulb.async_set_brightness.mock_calls == []

    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_COLOR_TEMP_KELVIN: 4000},
        blocking=True,
    )
    assert mocked_bulb.async_set_hsv.mock_calls == []
    assert mocked_bulb.async_set_rgb.mock_calls == []
    # Should call for the color mode change
    assert mocked_bulb.async_set_color_temp.mock_calls == [
        call(4000, duration=350, light_type=ANY)
    ]
    assert mocked_bulb.async_set_brightness.mock_calls == []
    mocked_bulb.async_set_color_temp.reset_mock()

    mocked_bulb.last_properties["color_mode"] = 2
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_COLOR_TEMP_KELVIN: 4000},
        blocking=True,
    )
    assert mocked_bulb.async_set_hsv.mock_calls == []
    assert mocked_bulb.async_set_rgb.mock_calls == []
    assert mocked_bulb.async_set_color_temp.mock_calls == []
    assert mocked_bulb.async_set_brightness.mock_calls == []

    mocked_bulb.last_properties["flowing"] = "1"

    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_COLOR_TEMP_KELVIN: 4000},
        blocking=True,
    )
    assert mocked_bulb.async_set_hsv.mock_calls == []
    assert mocked_bulb.async_set_rgb.mock_calls == []
    assert mocked_bulb.async_set_color_temp.mock_calls == [
        call(4000, duration=350, light_type=ANY)
    ]
    assert mocked_bulb.async_set_brightness.mock_calls == []
    mocked_bulb.async_set_color_temp.reset_mock()
    mocked_bulb.last_properties["flowing"] = "0"

    mocked_bulb.last_properties["color_mode"] = 3
    # This last change should generate a call even though
    # the color mode is the same since the HSV has changed
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_HS_COLOR: (5, 5)},
        blocking=True,
    )
    assert mocked_bulb.async_set_hsv.mock_calls == [
        call(5.0, 5.0, duration=350, light_type=ANY)
    ]
    assert mocked_bulb.async_set_rgb.mock_calls == []
    assert mocked_bulb.async_set_color_temp.mock_calls == []
    assert mocked_bulb.async_set_brightness.mock_calls == []
    mocked_bulb.async_set_hsv.reset_mock()

    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_HS_COLOR: (100, 35)},
        blocking=True,
    )
    assert mocked_bulb.async_set_hsv.mock_calls == []
    assert mocked_bulb.async_set_rgb.mock_calls == []
    assert mocked_bulb.async_set_color_temp.mock_calls == []
    assert mocked_bulb.async_set_brightness.mock_calls == []

    mocked_bulb.last_properties["flowing"] = "1"
    await hass.services.async_call(
        "light",
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_LIGHT, ATTR_HS_COLOR: (100, 35)},
        blocking=True,
    )
    assert mocked_bulb.async_set_hsv.mock_calls == [
        call(100.0, 35.0, duration=350, light_type=ANY)
    ]
    assert mocked_bulb.async_set_rgb.mock_calls == []
    assert mocked_bulb.async_set_color_temp.mock_calls == []
    assert mocked_bulb.async_set_brightness.mock_calls == []
    mocked_bulb.last_properties["flowing"] = "0"