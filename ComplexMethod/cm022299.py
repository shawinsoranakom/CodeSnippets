async def test_discovered_zeroconf(hass: HomeAssistant) -> None:
    """Test we can setup when discovered from zeroconf."""

    with _patch_get_info():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZEROCONF_DATA,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with (
        _patch_get_info(),
        patch(
            f"{MODULE}.async_setup_entry", return_value=True
        ) as mock_async_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == {CONF_HOST: IP_ADDRESS}
    assert result2["title"] == DEFAULT_ENTRY_TITLE
    assert mock_async_setup_entry.called

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    zc_data_new_ip = dataclasses.replace(ZEROCONF_DATA)
    zc_data_new_ip.ip_address = ip_address("127.0.0.2")

    with (
        _patch_get_info(),
        patch(
            f"{MODULE}.async_setup_entry", return_value=True
        ) as mock_async_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=zc_data_new_ip,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == "127.0.0.2"