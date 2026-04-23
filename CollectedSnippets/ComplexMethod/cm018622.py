async def test_flow(
    hass: HomeAssistant,
    mock_idrive_client: AsyncMock,
    mock_client: AsyncMock,
) -> None:
    """Test config flow success path."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ACCESS_KEY_ID: USER_INPUT[CONF_ACCESS_KEY_ID],
            CONF_SECRET_ACCESS_KEY: USER_INPUT[CONF_SECRET_ACCESS_KEY],
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bucket"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_BUCKET: USER_INPUT[CONF_BUCKET]},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test"
    assert result["data"] == USER_INPUT