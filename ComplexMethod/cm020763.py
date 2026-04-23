async def test_setup_connection_error(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_client: MagicMock,
    config_base: dict[str, Any],
    api_version: str,
    get_write_api: Any,
    test_exception: Exception,
    reason: str,
) -> None:
    """Test connection error during setup of InfluxDB v2."""
    write_api = get_write_api(mock_client)
    write_api.side_effect = test_exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": f"configure_v{api_version}"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == f"configure_v{api_version}"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        config_base,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": reason}

    write_api.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        config_base,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY