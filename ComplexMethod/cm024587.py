async def test_reauth_flow_auth_error(
    hass: HomeAssistant,
    mock_bsblan: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reauth flow with authentication error."""
    mock_config_entry.add_to_hass(hass)

    # Mock authentication error
    mock_bsblan.device.side_effect = BSBLANAuthError

    # Start reauth flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
    )

    _assert_form_result(result, "reauth_confirm")

    # Submit with wrong credentials
    result = await _configure_flow(
        hass,
        result["flow_id"],
        {
            CONF_PASSKEY: "wrong_passkey",
            CONF_USERNAME: "wrong_admin",
            CONF_PASSWORD: "wrong_password",
        },
    )

    _assert_form_result(result, "reauth_confirm", {"base": "invalid_auth"})

    # Verify that user input is preserved in the form after error
    data_schema = result.get("data_schema")
    assert data_schema is not None

    # Check that the form fields contain the previously entered values
    passkey_field = next(
        field for field in data_schema.schema if field.schema == CONF_PASSKEY
    )
    username_field = next(
        field for field in data_schema.schema if field.schema == CONF_USERNAME
    )

    assert passkey_field.default() == "wrong_passkey"
    assert username_field.default() == "wrong_admin"