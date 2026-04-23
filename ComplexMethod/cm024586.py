async def test_reauth_flow_success(
    hass: HomeAssistant,
    mock_bsblan: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful reauth flow."""
    mock_config_entry.add_to_hass(hass)

    # Start reauth flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": SOURCE_REAUTH,
            "entry_id": mock_config_entry.entry_id,
        },
    )

    _assert_form_result(result, "reauth_confirm")

    # Check that the form has the correct description placeholder
    assert result.get("description_placeholders") == {"name": "BSBLAN Setup"}

    # Check that existing values are preserved as defaults
    data_schema = result.get("data_schema")
    assert data_schema is not None

    # Complete reauth with new credentials
    result = await _configure_flow(
        hass,
        result["flow_id"],
        {
            CONF_PASSKEY: "new_passkey",
            CONF_USERNAME: "new_admin",
            CONF_PASSWORD: "new_password",
        },
    )

    _assert_abort_result(result, "reauth_successful")

    # Verify config entry was updated with new credentials
    assert mock_config_entry.data[CONF_PASSKEY] == "new_passkey"
    assert mock_config_entry.data[CONF_USERNAME] == "new_admin"
    assert mock_config_entry.data[CONF_PASSWORD] == "new_password"
    # Verify host and port remain unchanged
    assert mock_config_entry.data[CONF_HOST] == "127.0.0.1"
    assert mock_config_entry.data[CONF_PORT] == 80