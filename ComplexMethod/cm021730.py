async def test_config_flow_from_with_advanced_settings(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test if advanced settings show correctly."""
    config = MOCK_CONFIG.copy()
    config["ssl_cipher_list"] = "python_default"
    config["verify_ssl"] = True
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER, "show_advanced_options": True},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server",
        side_effect=TimeoutError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], config
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"]["base"] == "cannot_connect"
    assert "ssl_cipher_list" in result2["data_schema"].schema

    config["ssl_cipher_list"] = "modern"
    with patch(
        "homeassistant.components.imap.config_flow.connect_to_server"
    ) as mock_client:
        mock_client.return_value.search.return_value = (
            "OK",
            [b""],
        )
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], config
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "email@email.com"
    assert result3["data"] == config
    assert len(mock_setup_entry.mock_calls) == 1