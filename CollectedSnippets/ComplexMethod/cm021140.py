async def test_discovery_confirm_with_api_key_error(
    hass: HomeAssistant,
    bootstrap: Bootstrap,
    nvr: NVR,
    mock_api_bootstrap: Mock,
    mock_api_meta_info: Mock,
) -> None:
    """Test discovery confirm preserves API key in form data on error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
        data=UNIFI_DISCOVERY_DICT,
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"

    # Both attempts fail to test form_data preservation with API key
    mock_api_bootstrap.side_effect = NvrError("Connection failed")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test-username",
            "password": "test-password",
            "api_key": "test-api-key",
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert result["errors"] == {"base": "cannot_connect"}

    # Now provide working connection to complete the flow
    bootstrap.nvr = nvr
    mock_api_bootstrap.side_effect = None
    mock_api_bootstrap.return_value = bootstrap

    with (
        patch(
            "homeassistant.components.unifiprotect.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.unifiprotect.async_setup",
            return_value=True,
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
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == _async_unifi_mac_from_hass(
        DEVICE_MAC_ADDRESS.upper().replace(":", "")
    )