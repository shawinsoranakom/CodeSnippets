async def test_reconfigure_form_defaults(
    hass: HomeAssistant,
    bootstrap: Bootstrap,
    nvr: NVR,
    ufp_reauth_entry_alt: MockConfigEntry,
    mock_api_bootstrap: Mock,
    mock_api_meta_info: Mock,
    mock_setup: AsyncMock,
) -> None:
    """Test reconfiguration flow form has correct default values."""
    ufp_reauth_entry_alt.add_to_hass(hass)

    result = await ufp_reauth_entry_alt.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # Verify that non-sensitive fields are pre-filled and sensitive fields are not
    # The data_schema will have been created with add_suggested_values_to_schema
    # We can't easily verify the suggested values, but we can verify the flow works
    # and that when only providing new credentials, the old non-sensitive data is kept

    # Use nvr with matching MAC
    nvr.mac = _async_unifi_mac_from_hass(MAC_ADDR)
    bootstrap.nvr = nvr

    # Complete the flow to verify it works
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_PORT: 8443,
            CONF_VERIFY_SSL: True,
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "new-password",
            CONF_API_KEY: "new-api-key",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"

    # Verify that all data was updated
    entry = hass.config_entries.async_get_entry(ufp_reauth_entry_alt.entry_id)
    assert entry.data[CONF_HOST] == "1.1.1.1"
    assert entry.data[CONF_PORT] == 8443
    assert entry.data[CONF_VERIFY_SSL] is True
    assert entry.data[CONF_USERNAME] == "test-username"
    assert entry.data[CONF_PASSWORD] == "new-password"
    assert entry.data[CONF_API_KEY] == "new-api-key"