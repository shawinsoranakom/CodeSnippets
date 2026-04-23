async def test_form_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_nextdns_client: AsyncMock,
    mock_nextdns: AsyncMock,
    exc: Exception,
    base_error: str,
) -> None:
    """Test we handle errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    mock_nextdns.create.side_effect = exc

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "fake_api_key"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": base_error}

    mock_nextdns.create.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "fake_api_key"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "profiles"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PROFILE_NAME: "Fake Profile"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Fake Profile"
    assert result["data"][CONF_API_KEY] == "fake_api_key"
    assert result["data"][CONF_PROFILE_ID] == "xyz12"
    assert result["result"].unique_id == "xyz12"
    assert len(mock_setup_entry.mock_calls) == 1