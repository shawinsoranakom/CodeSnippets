async def test_manual_camera_no_live_view(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
    mock_connect: AsyncMock,
) -> None:
    """Test manual camera."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: IP_ADDRESS3}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "camera_auth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_LIVE_VIEW: False,
            CONF_USERNAME: "camuser",
            CONF_PASSWORD: "campass",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_CAMERA_CREDENTIALS not in result["data"]
    assert result["data"][CONF_LIVE_VIEW] is False