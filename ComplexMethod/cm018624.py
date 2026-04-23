async def test_flow_no_buckets(
    hass: HomeAssistant,
    mock_idrive_client: AsyncMock,
    mock_client: AsyncMock,
) -> None:
    """Test we show an error when no buckets are returned."""
    # Start flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # First attempt: empty bucket list -> error
    mock_client.list_buckets.return_value = {"Buckets": []}
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "no_buckets"}

    # Second attempt: fix and finish to CREATE_ENTRY
    mock_client.list_buckets.return_value = {
        "Buckets": [{"Name": USER_INPUT[CONF_BUCKET]}]
    }
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