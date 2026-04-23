async def test_user_errors(
    hass: HomeAssistant,
    mock_pyvlx: AsyncMock,
    exception: Exception,
    error: str,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test starting a flow by user but with exceptions."""

    mock_pyvlx.connect.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "NotAStrongPassword",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error}

    mock_pyvlx.connect.assert_called_once()

    mock_pyvlx.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "NotAStrongPassword",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY