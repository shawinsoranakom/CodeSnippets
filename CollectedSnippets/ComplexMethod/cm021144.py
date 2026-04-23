async def test_reauth_credential_update(
    hass: HomeAssistant,
    bootstrap: Bootstrap,
    nvr: NVR,
    ufp_reauth_entry: MockConfigEntry,
    mock_api_bootstrap: Mock,
    mock_api_meta_info: Mock,
    input_credentials: dict[str, str],
    expected_credentials: dict[str, str],
) -> None:
    """Test reauth with various credential update scenarios."""
    ufp_reauth_entry.add_to_hass(hass)

    result = await ufp_reauth_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    nvr.mac = _async_unifi_mac_from_hass(MAC_ADDR)
    bootstrap.nvr = nvr
    with (
        patch(
            "homeassistant.components.unifiprotect.async_setup",
            return_value=True,
        ),
        patch(
            "homeassistant.components.unifiprotect.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            input_credentials,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert ufp_reauth_entry.data[CONF_USERNAME] == expected_credentials[CONF_USERNAME]
    assert ufp_reauth_entry.data[CONF_PASSWORD] == expected_credentials[CONF_PASSWORD]
    assert ufp_reauth_entry.data[CONF_API_KEY] == expected_credentials[CONF_API_KEY]
    # Host should remain unchanged
    assert ufp_reauth_entry.data[CONF_HOST] == "1.1.1.1"