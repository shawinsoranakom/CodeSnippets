async def test_user_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_pyvlx: AsyncMock,
) -> None:
    """Test starting a flow by user with valid values."""
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

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "127.0.0.1"
    assert result["data"] == {
        CONF_HOST: "127.0.0.1",
        CONF_PASSWORD: "NotAStrongPassword",
    }
    assert not result["result"].unique_id

    mock_pyvlx.disconnect.assert_called_once()
    mock_pyvlx.connect.assert_called_once()