async def test_options(hass: HomeAssistant, mock_api: MagicMock) -> None:
    """Test updating options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="SpeedTest",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SERVER_NAME: "Country1 - Sponsor1 - Server1",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_SERVER_NAME: "Country1 - Sponsor1 - Server1",
        CONF_SERVER_ID: "1",
    }
    await hass.async_block_till_done()

    # test setting server name to "*Auto Detect"
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SERVER_NAME: "*Auto Detect",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_SERVER_NAME: "*Auto Detect",
        CONF_SERVER_ID: None,
    }