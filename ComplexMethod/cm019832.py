async def test_dhcp_discovery(hass: HomeAssistant, client: MagicMock) -> None:
    """Test we can process the discovery from dhcp."""
    with patch(
        "homeassistant.components.balboa.config_flow.SpaClient.__aenter__",
        return_value=client,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=TEST_DHCP_SERVICE_INFO,
        )

        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == "FakeSpa"
        assert result["data"] == TEST_DATA
        assert result["result"].unique_id == TEST_MAC

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=TEST_DHCP_SERVICE_INFO,
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"