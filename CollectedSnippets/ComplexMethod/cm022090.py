async def test_user_flow_is_not_blocked_by_discovery(hass: HomeAssistant) -> None:
    """Test we can setup from the user flow when there is also a discovery."""
    discovery_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="mock_hostname",
            name="testfan",
            port=None,
            properties={"name": "My Fan", "model": "Haiku", "uuid": MOCK_UUID},
            type="mock_type",
        ),
    )
    assert discovery_result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        _patch_device_config_flow(),
        patch(
            "homeassistant.components.baf.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_IP_ADDRESS: "127.0.0.1"},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == MOCK_NAME
    assert result2["data"] == {CONF_IP_ADDRESS: "127.0.0.1"}
    assert len(mock_setup_entry.mock_calls) == 1