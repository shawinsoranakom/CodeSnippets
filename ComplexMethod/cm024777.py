async def test_manual(hass: HomeAssistant) -> None:
    """Test manually setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    # Cannot connect (timeout)
    mocked_bulb = _mocked_bulb(cannot_connect=True)
    with (
        _patch_discovery(no_device=True),
        _patch_discovery_timeout(),
        _patch_discovery_interval(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": "cannot_connect"}

    # Cannot connect (error)
    with (
        _patch_discovery(no_device=True),
        _patch_discovery_timeout(),
        _patch_discovery_interval(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
    assert result3["errors"] == {"base": "cannot_connect"}

    # Success
    mocked_bulb = _mocked_bulb()
    with (
        _patch_discovery(),
        _patch_discovery_timeout(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
        patch(f"{MODULE}.async_setup", return_value=True),
        patch(f"{MODULE}.async_setup_entry", return_value=True),
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
        await hass.async_block_till_done()
    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == "Color 0x15243f"
    assert result4["data"] == {
        CONF_HOST: IP_ADDRESS,
        CONF_ID: "0x000000000015243f",
        CONF_MODEL: MODEL,
    }

    # Duplicate
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    mocked_bulb = _mocked_bulb()
    with (
        _patch_discovery(no_device=True),
        _patch_discovery_timeout(),
        _patch_discovery_interval(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"