async def test_user_flow(hass: HomeAssistant, bootstrap: Bootstrap, nvr: NVR) -> None:
    """Test successful user flow creates config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    bootstrap.nvr = nvr
    with (
        patch(
            "homeassistant.components.unifiprotect.config_flow.ProtectApiClient.get_bootstrap",
            return_value=bootstrap,
        ),
        patch(
            "homeassistant.components.unifiprotect.config_flow.ProtectApiClient.get_meta_info",
            return_value=None,
        ),
        patch(
            "homeassistant.components.unifiprotect.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.unifiprotect.async_setup",
            return_value=True,
        ) as mock_setup,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "username": "test-username",
                "password": "test-password",
                "api_key": "test-api-key",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "UnifiProtect"
    assert result["data"] == {
        "host": "1.1.1.1",
        "username": "test-username",
        "password": "test-password",
        "api_key": "test-api-key",
        "id": "UnifiProtect",
        "port": 443,
        "verify_ssl": False,
    }
    assert result["result"].unique_id == _async_unifi_mac_from_hass(nvr.mac)
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_setup.mock_calls) == 1