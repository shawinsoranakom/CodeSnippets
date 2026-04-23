async def test_user_flow_unconnectable(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_remote_control,
) -> None:
    """Test we can setup an entry."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM

    mock_remote_control._instance_mock.check_connectable = AsyncMock(
        side_effect=SkyBoxConnectionError("Example")
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: SAMPLE_CONFIG[CONF_HOST]},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    assert len(mock_setup_entry.mock_calls) == 0

    mock_remote_control._instance_mock.check_connectable = AsyncMock(True)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: SAMPLE_CONFIG[CONF_HOST]},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == SAMPLE_CONFIG

    assert len(mock_setup_entry.mock_calls) == 1