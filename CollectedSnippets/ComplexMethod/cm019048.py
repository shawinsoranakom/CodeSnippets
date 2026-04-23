async def test_zeroconf(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we get the form."""
    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        return_value="aa:bb:cc:dd:ee:ff",
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": SOURCE_ZEROCONF},
        )
        context = next(
            flow["context"]
            for flow in hass.config_entries.flow.async_progress()
            if flow["flow_id"] == result["flow_id"]
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert context["title_placeholders"]["host"] == "10.10.2.3"
    assert context["confirm_only"] is True

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "10.10.2.3"
    assert result["data"] == {"host": "10.10.2.3"}
    assert len(mock_setup_entry.mock_calls) == 1