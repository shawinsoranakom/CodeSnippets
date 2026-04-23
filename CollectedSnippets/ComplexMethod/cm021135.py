async def test_form_reauth_auth(
    hass: HomeAssistant,
    bootstrap: Bootstrap,
    nvr: NVR,
    ufp_reauth_entry: MockConfigEntry,
) -> None:
    """Test we handle reauth auth."""
    ufp_reauth_entry.add_to_hass(hass)

    result = await ufp_reauth_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert flows[0]["context"]["title_placeholders"] == {
        "ip_address": "1.1.1.1",
        "name": "Mock Title",
    }

    # Verify that non-sensitive fields are pre-filled and sensitive fields are not
    # The data_schema will have been created with add_suggested_values_to_schema
    # We can't easily verify the suggested values, but we can verify the flow works
    # and that when only providing new credentials, the old non-sensitive data is kept

    with (
        patch(
            "homeassistant.components.unifiprotect.config_flow.ProtectApiClient.get_bootstrap",
            side_effect=NotAuthorized,
        ),
        patch(
            "homeassistant.components.unifiprotect.config_flow.ProtectApiClient.get_meta_info",
            return_value=None,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "api_key": "test-api-key",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"password": "invalid_auth"}
    assert result["step_id"] == "reauth_confirm"

    bootstrap.nvr = nvr
    with (
        patch(
            "homeassistant.components.unifiprotect.config_flow.ProtectApiClient.get_bootstrap",
            return_value=bootstrap,
        ),
        patch(
            "homeassistant.components.unifiprotect.async_setup",
            return_value=True,
        ) as mock_setup,
        patch(
            "homeassistant.components.unifiprotect.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.unifiprotect.config_flow.ProtectApiClient.get_meta_info",
            return_value=None,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "new-password",
                "api_key": "test-api-key",
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert len(mock_setup.mock_calls) == 1

    # Verify that non-sensitive data was preserved when only credentials were updated
    assert ufp_reauth_entry.data[CONF_HOST] == "1.1.1.1"
    assert ufp_reauth_entry.data[CONF_PORT] == 443
    assert ufp_reauth_entry.data[CONF_VERIFY_SSL] is False
    assert ufp_reauth_entry.data[CONF_USERNAME] == "test-username"
    assert ufp_reauth_entry.data[CONF_PASSWORD] == "new-password"
    assert ufp_reauth_entry.data[CONF_API_KEY] == "test-api-key"