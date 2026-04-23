async def test_user_form_can_create_when_already_discovered(
    hass: HomeAssistant,
) -> None:
    """Test we get the user initiated form can create when already discovered."""

    with patch_bond_version(), patch_bond_token():
        zc_result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("127.0.0.1"),
                ip_addresses=[ip_address("127.0.0.1")],
                hostname="mock_hostname",
                name="ZXXX12345.some-other-tail-info",
                port=None,
                properties={},
                type="mock_type",
            ),
        )
        assert zc_result["type"] is FlowResultType.FORM
        assert zc_result["errors"] == {}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch_bond_version(return_value={"bondid": "ZXXX12345"}),
        patch_bond_device_ids(return_value=["f6776c11", "f6776c12"]),
        patch_bond_bridge(),
        patch_bond_device_properties(),
        patch_bond_device(),
        patch_bond_device_state(),
        _patch_async_setup_entry() as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "bond-name"
    assert result2["data"] == {
        CONF_HOST: "some host",
        CONF_ACCESS_TOKEN: "test-token",
    }
    assert result2["result"].unique_id == "ZXXX12345"
    assert len(mock_setup_entry.mock_calls) == 1