async def test_flow_bucket_step_options_from_s3_list_buckets(
    hass: HomeAssistant,
    mock_idrive_client: AsyncMock,
    mock_client: AsyncMock,
) -> None:
    """Test bucket step shows dropdown options coming from S3 list_buckets()."""
    # Start flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # S3 list_buckets returns our test payload
    mock_client.list_buckets.return_value = {
        "Buckets": [{"Name": "bucket1"}, {"Name": "bucket2"}]
    }

    # Submit credentials
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bucket"

    # Extract dropdown options from selector in schema
    schema = result["data_schema"].schema
    selector = schema[vol.Required(CONF_BUCKET)]
    assert isinstance(selector, SelectSelector)

    cfg = selector.config
    options = cfg["options"] if isinstance(cfg, dict) else cfg.options

    assert options == ["bucket1", "bucket2"]

    # Continue to finish to CREATE_ENTRY
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {CONF_BUCKET: "bucket1"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "bucket1"
    assert result["data"][CONF_BUCKET] == "bucket1"