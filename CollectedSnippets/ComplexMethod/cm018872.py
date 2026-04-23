async def test_discovered_by_dhcp_partial_udp_response_fallback_tcp(
    hass: HomeAssistant,
) -> None:
    """Test we can setup when discovered from dhcp but part of the udp response is missing."""

    with _patch_discovery(no_device=True), _patch_wifibulb():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=DHCP_DISCOVERY
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with (
        _patch_discovery(device=FLUX_DISCOVERY_PARTIAL),
        _patch_wifibulb(),
        patch(f"{MODULE}.async_setup", return_value=True) as mock_async_setup,
        patch(
            f"{MODULE}.async_setup_entry", return_value=True
        ) as mock_async_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == {
        CONF_HOST: IP_ADDRESS,
        CONF_MODEL_NUM: MODEL_NUM,
        CONF_MODEL_DESCRIPTION: MODEL_DESCRIPTION,
    }
    assert result2["title"] == "Bulb RGBCW DDEEFF"
    assert mock_async_setup.called
    assert mock_async_setup_entry.called