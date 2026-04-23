async def test_discovered_zeroconf(hass: HomeAssistant) -> None:
    """Test we can setup when discovered from zeroconf."""

    mocked_bulb = _mocked_bulb()
    with (
        _patch_discovery(),
        _patch_discovery_interval(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZEROCONF_DATA,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with (
        _patch_discovery(),
        _patch_discovery_interval(),
        patch(f"{MODULE}.async_setup", return_value=True) as mock_async_setup,
        patch(
            f"{MODULE}.async_setup_entry", return_value=True
        ) as mock_async_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == {
        CONF_HOST: IP_ADDRESS,
        CONF_ID: "0x000000000015243f",
        CONF_MODEL: MODEL,
    }
    assert mock_async_setup.called
    assert mock_async_setup_entry.called

    mocked_bulb = _mocked_bulb()
    with (
        _patch_discovery(),
        _patch_discovery_interval(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZEROCONF_DATA,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"

    mocked_bulb = _mocked_bulb()
    with (
        _patch_discovery(),
        _patch_discovery_interval(),
        patch(f"{MODULE_CONFIG_FLOW}.AsyncBulb", return_value=mocked_bulb),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=SSDP_INFO,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"