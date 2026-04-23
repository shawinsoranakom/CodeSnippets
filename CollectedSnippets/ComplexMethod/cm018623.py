async def test_flow_list_buckets_errors(
    hass: HomeAssistant,
    mock_idrive_client: AsyncMock,
    mock_client: AsyncMock,
    exception: Exception,
    errors: dict[str, str],
) -> None:
    """Test errors when listing buckets."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # First attempt: fail
    mock_client.list_buckets.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == errors

    # Second attempt: fix and finish to CREATE_ENTRY
    mock_client.list_buckets.side_effect = None

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
    assert result["title"] == "test"
    assert result["data"] == USER_INPUT