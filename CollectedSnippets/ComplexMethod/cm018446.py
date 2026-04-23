async def test_flow_errors(
    hass: HomeAssistant,
    mock_madvr_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test error handling in config flow."""
    mock_madvr_client.open_connection.side_effect = TimeoutError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_CONFIG[CONF_HOST], CONF_PORT: MOCK_CONFIG[CONF_PORT]},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    mock_madvr_client.open_connection.side_effect = None
    mock_madvr_client.connected = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_CONFIG[CONF_HOST], CONF_PORT: MOCK_CONFIG[CONF_PORT]},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    mock_madvr_client.connected = True
    mock_madvr_client.mac_address = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_CONFIG[CONF_HOST], CONF_PORT: MOCK_CONFIG[CONF_PORT]},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_mac"}

    # ensure an error is recoverable
    mock_madvr_client.mac_address = MOCK_MAC
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_CONFIG[CONF_HOST], CONF_PORT: MOCK_CONFIG[CONF_PORT]},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {
        CONF_HOST: MOCK_CONFIG[CONF_HOST],
        CONF_PORT: MOCK_CONFIG[CONF_PORT],
    }

    # Verify method calls
    assert mock_madvr_client.open_connection.call_count == 4
    assert mock_madvr_client.async_add_tasks.call_count == 2
    # the first call will not call this due to timeout as expected
    assert mock_madvr_client.async_cancel_tasks.call_count == 2