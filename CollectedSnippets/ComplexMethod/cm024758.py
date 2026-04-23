async def test_camera_errors(
    hass: HomeAssistant,
    mock_ezviz_client: AsyncMock,
    mock_test_rtsp_auth: AsyncMock,
    mock_config_entry: MockConfigEntry,
    exception: Exception,
    error: str,
) -> None:
    """Test the camera flow with errors."""

    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_INTEGRATION_DISCOVERY},
        data={
            ATTR_SERIAL: "C666666",
            CONF_USERNAME: None,
            CONF_PASSWORD: None,
            CONF_IP_ADDRESS: "127.0.0.1",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["errors"] == {}

    mock_ezviz_client.login.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["errors"] == {"base": error}

    mock_ezviz_client.login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "C666666"
    assert result["data"] == {
        CONF_TYPE: ATTR_TYPE_CAMERA,
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
    }
    assert result["result"].unique_id == "C666666"