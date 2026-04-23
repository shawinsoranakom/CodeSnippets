async def test_config_flow_errors(
    hass: HomeAssistant, reolink_host: MagicMock, mock_setup_entry: MagicMock
) -> None:
    """Successful flow manually initialized by the user after some errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    reolink_host.is_admin = False
    reolink_host.user_level = "guest"
    reolink_host.unsubscribe.side_effect = ReolinkError("Test error")
    reolink_host.logout.side_effect = ReolinkError("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_HOST: TEST_HOST,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_USERNAME: "not_admin"}

    reolink_host.is_admin = True
    reolink_host.user_level = "admin"
    reolink_host.get_host_data.side_effect = ReolinkError("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_HOST: TEST_HOST,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_HOST: "cannot_connect"}

    reolink_host.get_host_data.side_effect = ReolinkWebhookException("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_HOST: TEST_HOST,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "webhook_exception"}

    reolink_host.get_host_data.side_effect = json.JSONDecodeError(
        "test_error", "test", 1
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_HOST: TEST_HOST,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_HOST: "unknown"}

    reolink_host.get_host_data.side_effect = CredentialsInvalidError("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_HOST: TEST_HOST,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_PASSWORD: "invalid_auth"}

    reolink_host.get_host_data.side_effect = LoginFirmwareError("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_HOST: TEST_HOST,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "update_needed"}

    reolink_host.valid_password.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_HOST: TEST_HOST,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_PASSWORD: "password_incompatible"}

    reolink_host.valid_password.return_value = True
    reolink_host.get_host_data.side_effect = ApiError("Test error")
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_HOST: TEST_HOST,
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_HOST: "api_error"}

    reolink_host.get_host_data.reset_mock(side_effect=True)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_HOST: TEST_HOST,
            CONF_PORT: TEST_PORT,
            CONF_USE_HTTPS: TEST_USE_HTTPS,
            CONF_BC_PORT: TEST_BC_PORT,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_NVR_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
        CONF_PORT: TEST_PORT,
        CONF_USE_HTTPS: TEST_USE_HTTPS,
        CONF_SUPPORTS_PRIVACY_MODE: TEST_PRIVACY,
        CONF_BC_PORT: TEST_BC_PORT,
        CONF_BC_ONLY: False,
    }
    assert result["options"] == {
        CONF_PROTOCOL: DEFAULT_PROTOCOL,
    }