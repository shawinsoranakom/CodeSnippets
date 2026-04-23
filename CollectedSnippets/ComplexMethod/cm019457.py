async def test_discovery_no_devices(
    hass: HomeAssistant, mock_discover, mock_s20, mock_setup_entry
) -> None:
    """Discovery with no found devices should go to discovery_failed and recover via edit."""
    mock_discover.return_value = {}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "start_discovery"}
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] == FlowResultType.MENU
    assert result["step_id"] == "discovery_failed"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "edit"}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "edit"

    mock_s20.return_value._mac = b"\xaa\xbb\xcc\xdd\xee\xff"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: "192.168.1.10", CONF_MAC: "aa:bb:cc:dd:ee:ff"},
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{DEFAULT_NAME} (192.168.1.10)"
    assert result["data"][CONF_HOST] == "192.168.1.10"
    assert result["data"][CONF_MAC] == "aa:bb:cc:dd:ee:ff"