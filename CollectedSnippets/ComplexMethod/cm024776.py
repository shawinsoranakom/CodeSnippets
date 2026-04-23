async def test_import(hass: HomeAssistant) -> None:
    """Test import from yaml."""
    config = {
        CONF_NAME: DEFAULT_NAME,
        CONF_HOST: IP_ADDRESS,
        CONF_TRANSITION: DEFAULT_TRANSITION,
        CONF_MODE_MUSIC: DEFAULT_MODE_MUSIC,
        CONF_SAVE_ON_CHANGE: DEFAULT_SAVE_ON_CHANGE,
        CONF_NIGHTLIGHT_SWITCH_TYPE: NIGHTLIGHT_SWITCH_TYPE_LIGHT,
    }

    # Cannot connect
    mocked_bulb = _mocked_bulb(cannot_connect=True)
    with (
        _patch_discovery(no_device=True),
        _patch_discovery_timeout(),
        _patch_discovery_interval(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=config
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"

    # Success
    mocked_bulb = _mocked_bulb()
    with (
        _patch_discovery(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
        patch(f"{MODULE}.async_setup", return_value=True) as mock_setup,
        patch(f"{MODULE}.async_setup_entry", return_value=True) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=config
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {
        CONF_NAME: DEFAULT_NAME,
        CONF_HOST: IP_ADDRESS,
        CONF_TRANSITION: DEFAULT_TRANSITION,
        CONF_MODE_MUSIC: DEFAULT_MODE_MUSIC,
        CONF_SAVE_ON_CHANGE: DEFAULT_SAVE_ON_CHANGE,
        CONF_NIGHTLIGHT_SWITCH: True,
    }
    await hass.async_block_till_done()
    mock_setup.assert_called_once()
    mock_setup_entry.assert_called_once()

    # Duplicate
    mocked_bulb = _mocked_bulb()
    with (
        _patch_discovery(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data=config
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"