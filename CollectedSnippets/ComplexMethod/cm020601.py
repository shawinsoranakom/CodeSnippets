async def test_update_missing_mac_unique_id_added_ssdp_location_main_tv_agent_st_updated_from_ssdp(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test missing mac and unique id with outdated ssdp_location with the correct st added via ssdp."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            **ENTRYDATA_LEGACY,
            CONF_SSDP_RENDERING_CONTROL_LOCATION: "https://1.2.3.4:555/test",
            CONF_SSDP_MAIN_TV_AGENT_LOCATION: "https://1.2.3.4:555/test",
        },
        unique_id=None,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=MOCK_SSDP_DATA_MAIN_TV_AGENT_ST,
    )
    await hass.async_block_till_done()
    assert len(mock_setup_entry.mock_calls) == 1

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_MAC] == "aa:bb:aa:aa:aa:aa"
    # Main TV Agent ST, ssdp location should change
    assert (
        entry.data[CONF_SSDP_MAIN_TV_AGENT_LOCATION] == "http://10.10.12.34:7676/smp_2_"
    )
    # Rendering control should not be affected
    assert (
        entry.data[CONF_SSDP_RENDERING_CONTROL_LOCATION] == "https://1.2.3.4:555/test"
    )
    assert entry.unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"