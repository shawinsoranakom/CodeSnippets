async def test_manual_camera(
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

    # Test no username or pass
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_LIVE_VIEW: True,
            CONF_USERNAME: "camuser",
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "camera_auth_confirm"
    assert result["errors"] == {"base": "camera_creds"}

    # Test unknown error
    with (
        patch(
            "homeassistant.components.stream.async_check_stream_client_error",
            side_effect=stream.StreamOpenClientError(
                "Stream was not found", error_code=stream.StreamClientError.NotFound
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LIVE_VIEW: True,
                CONF_USERNAME: "camuser",
                CONF_PASSWORD: "campass",
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "camera_auth_confirm"
    assert result["errors"] == {"base": "cannot_connect_camera"}
    assert "error" in result["description_placeholders"]

    # Test unknown error
    with (
        patch(
            "homeassistant.components.stream.async_check_stream_client_error",
            side_effect=stream.StreamOpenClientError(
                "Request is unauthorized",
                error_code=stream.StreamClientError.Unauthorized,
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LIVE_VIEW: True,
                CONF_USERNAME: "camuser",
                CONF_PASSWORD: "campass",
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "camera_auth_confirm"
    assert result["errors"] == {"base": "invalid_camera_auth"}

    with patch(
        "homeassistant.components.stream.async_check_stream_client_error",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LIVE_VIEW: True,
                CONF_USERNAME: "camuser",
                CONF_PASSWORD: "campass",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_CAMERA_CREDENTIALS] == {
        CONF_USERNAME: "camuser",
        CONF_PASSWORD: "campass",
    }
    assert result["data"][CONF_LIVE_VIEW] is True