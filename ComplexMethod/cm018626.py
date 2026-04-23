async def test_flow_get_region_endpoint_error(
    hass: HomeAssistant,
    mock_idrive_client: AsyncMock,
    mock_client: AsyncMock,
    exception: Exception,
    expected_error: str,
) -> None:
    """Test user step error mapping when resolving region endpoint via client."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # First attempt: fail endpoint resolution
    mock_idrive_client.get_region_endpoint.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": expected_error}

    # Second attempt: fix and finish to CREATE_ENTRY
    mock_idrive_client.get_region_endpoint.side_effect = None
    mock_idrive_client.get_region_endpoint.return_value = USER_INPUT[CONF_ENDPOINT_URL]

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bucket"

    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {CONF_BUCKET: USER_INPUT[CONF_BUCKET]},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == USER_INPUT