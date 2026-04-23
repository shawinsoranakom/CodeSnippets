async def test_dhcp_discovery(hass: HomeAssistant) -> None:
    """Test we can process the discovery from dhcp."""

    mocked_yeti = await create_mocked_yeti()
    with patch_config_flow_yeti(mocked_yeti), _patch_setup():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=CONF_DHCP_FLOW,
        )
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == MANUFACTURER
        assert result["data"] == CONF_DATA
        assert result["result"].unique_id == MAC

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=CONF_DHCP_FLOW,
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"