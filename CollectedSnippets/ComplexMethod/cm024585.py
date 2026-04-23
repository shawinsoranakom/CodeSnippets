async def test_authentication_error(
    hass: HomeAssistant,
    mock_bsblan: MagicMock,
) -> None:
    """Test we show user form on BSBLan authentication error with field preservation."""
    mock_bsblan.device.side_effect = BSBLANAuthError

    user_input = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 8080,
        CONF_PASSKEY: "secret",
        CONF_USERNAME: "testuser",
        CONF_PASSWORD: "wrongpassword",
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=user_input,
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"base": "invalid_auth"}
    assert result.get("step_id") == "user"

    # Verify that user input is preserved in the form
    data_schema = result.get("data_schema")
    assert data_schema is not None

    # Check that the form fields contain the previously entered values
    host_field = next(
        field for field in data_schema.schema if field.schema == CONF_HOST
    )
    port_field = next(
        field for field in data_schema.schema if field.schema == CONF_PORT
    )
    passkey_field = next(
        field for field in data_schema.schema if field.schema == CONF_PASSKEY
    )
    username_field = next(
        field for field in data_schema.schema if field.schema == CONF_USERNAME
    )
    password_field = next(
        field for field in data_schema.schema if field.schema == CONF_PASSWORD
    )

    # The defaults are callable functions, so we need to call them
    assert host_field.default() == "192.168.1.100"
    assert port_field.default() == 8080
    assert passkey_field.default() == "secret"
    assert username_field.default() == "testuser"
    # Password should never be pre-filled for security reasons
    assert password_field.default is vol.UNDEFINED