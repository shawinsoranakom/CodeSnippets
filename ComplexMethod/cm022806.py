async def test_default_state(hass: HomeAssistant) -> None:
    """Test light switch default state."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: "switch.test",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: Platform.LIGHT,
        },
        title="Christmas Tree Lights",
        version=SwitchAsXConfigFlowHandler.VERSION,
        minor_version=SwitchAsXConfigFlowHandler.MINOR_VERSION,
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("light.christmas_tree_lights")
    assert state is not None
    assert state.state == "unavailable"
    assert state.attributes["supported_features"] == 0
    assert state.attributes.get(ATTR_BRIGHTNESS) is None
    assert state.attributes.get(ATTR_HS_COLOR) is None
    assert state.attributes.get(ATTR_COLOR_TEMP_KELVIN) is None
    assert state.attributes.get(ATTR_EFFECT_LIST) is None
    assert state.attributes.get(ATTR_EFFECT) is None
    assert state.attributes.get(ATTR_SUPPORTED_COLOR_MODES) == [ColorMode.ONOFF]
    assert state.attributes.get(ATTR_COLOR_MODE) is None