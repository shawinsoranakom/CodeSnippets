async def test_user_exceptions(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_vivotek_camera: AsyncMock,
    exception: Exception,
    error: str,
) -> None:
    """Test user initiated flow with exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    mock_vivotek_camera.get_mac.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_DATA
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error}

    mock_vivotek_camera.get_mac.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_DATA
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY