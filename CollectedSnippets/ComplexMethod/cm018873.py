async def test_options(hass: HomeAssistant) -> None:
    """Test options flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: IP_ADDRESS},
        title=IP_ADDRESS,
        options={
            CONF_CUSTOM_EFFECT_COLORS: "[255,0,0], [0,0,255]",
            CONF_CUSTOM_EFFECT_SPEED_PCT: 30,
            CONF_CUSTOM_EFFECT_TRANSITION: TRANSITION_STROBE,
        },
        unique_id=MAC_ADDRESS,
    )
    config_entry.add_to_hass(hass)

    with _patch_discovery(), _patch_wifibulb():
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    user_input = {
        CONF_CUSTOM_EFFECT_COLORS: "[0,0,255], [255,0,0]",
        CONF_CUSTOM_EFFECT_SPEED_PCT: 50,
        CONF_CUSTOM_EFFECT_TRANSITION: TRANSITION_JUMP,
    }
    with _patch_discovery(), _patch_wifibulb():
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input
        )
        await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == user_input
    assert result2["data"] == config_entry.options
    assert hass.states.get("light.bulb_rgbcw_ddeeff") is not None