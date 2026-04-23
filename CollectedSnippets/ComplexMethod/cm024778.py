async def test_options(hass: HomeAssistant) -> None:
    """Test options flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: IP_ADDRESS, CONF_NAME: NAME, CONF_DETECTED_MODEL: MODEL},
    )
    config_entry.add_to_hass(hass)

    mocked_bulb = _mocked_bulb()
    with _patch_discovery(), patch(f"{MODULE}.AsyncBulb", return_value=mocked_bulb):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    config = {
        CONF_NAME: NAME,
        CONF_MODEL: MODEL,
        CONF_TRANSITION: DEFAULT_TRANSITION,
        CONF_MODE_MUSIC: DEFAULT_MODE_MUSIC,
        CONF_SAVE_ON_CHANGE: DEFAULT_SAVE_ON_CHANGE,
        CONF_NIGHTLIGHT_SWITCH: DEFAULT_NIGHTLIGHT_SWITCH,
    }
    assert config_entry.options == config
    assert hass.states.get(f"light.{NAME}_nightlight") is None

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    config[CONF_NIGHTLIGHT_SWITCH] = True
    user_input = {**config}
    user_input.pop(CONF_NAME)
    user_input.pop(CONF_MODEL)
    with _patch_discovery(), patch(f"{MODULE}.AsyncBulb", return_value=mocked_bulb):
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input
        )
        await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == config
    assert result2["data"] == config_entry.options
    assert hass.states.get(f"light.{NAME}_nightlight") is not None