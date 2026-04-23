async def test_full_flow(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_vivotek_camera: AsyncMock
) -> None:
    """Test full user initiated flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_DATA
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == USER_DATA
    assert result["options"] == {CONF_FRAMERATE: DEFAULT_FRAMERATE}
    assert result["result"].unique_id == "11:22:33:44:55:66"