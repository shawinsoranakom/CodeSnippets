async def test_dhcp_discovery(hass: HomeAssistant) -> None:
    """Test DHCP discovery."""

    with patch_bond_version(), patch_bond_token():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip="127.0.0.1",
                hostname="Bond-KVPRBDJ45842",
                macaddress="3c6a2c1c8c80",
            ),
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {}

    with (
        patch_bond_version(return_value={"bondid": "KVPRBDJ45842"}),
        patch_bond_bridge(),
        patch_bond_device_ids(),
        _patch_async_setup_entry() as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ACCESS_TOKEN: "test-token"},
        )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "bond-name"
    assert result2["data"] == {
        CONF_HOST: "127.0.0.1",
        CONF_ACCESS_TOKEN: "test-token",
    }
    assert result2["result"].unique_id == "KVPRBDJ45842"
    assert len(mock_setup_entry.mock_calls) == 1