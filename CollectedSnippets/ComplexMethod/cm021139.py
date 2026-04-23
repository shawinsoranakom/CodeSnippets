async def test_discovered_by_unifi_discovery_direct_connect_on_different_interface_resolver_fails(
    hass: HomeAssistant, bootstrap: Bootstrap, nvr: NVR
) -> None:
    """Test we can still configure if the resolver fails."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "y.ui.direct",
            "username": "test-username",
            "password": "test-password",
            "api_key": "test-api-key",
            "id": "UnifiProtect",
            "port": 443,
            "verify_ssl": True,
        },
        unique_id="FFFFFFAAAAAA",
    )
    mock_config.runtime_data = Mock(async_stop=AsyncMock())
    mock_config.add_to_hass(hass)

    other_ip_dict = UNIFI_DISCOVERY_DICT.copy()
    other_ip_dict["source_ip"] = "127.0.0.2"
    other_ip_dict["direct_connect_domain"] = "nomatchsameip.ui.direct"

    with (
        patch.object(hass.loop, "getaddrinfo", side_effect=OSError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data=other_ip_dict,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert flows[0]["context"]["title_placeholders"] == {
        "ip_address": "127.0.0.2",
        "name": "unvr",
    }

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
                "username": "test-username",
                "password": "test-password",
                "api_key": "test-api-key",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "UnifiProtect"
    assert result["data"] == {
        "host": "nomatchsameip.ui.direct",
        "username": "test-username",
        "password": "test-password",
        "api_key": "test-api-key",
        "id": "UnifiProtect",
        "port": 443,
        "verify_ssl": True,
    }
    assert result["result"].unique_id == _async_unifi_mac_from_hass(
        DEVICE_MAC_ADDRESS.upper().replace(":", "")
    )
    assert len(mock_setup_entry.mock_calls) == 2
    assert len(mock_setup.mock_calls) == 1