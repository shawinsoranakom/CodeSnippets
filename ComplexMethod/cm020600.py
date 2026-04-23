async def test_update_old_entry(hass: HomeAssistant) -> None:
    """Test update of old entry sets unique id."""
    entry = MockConfigEntry(domain=DOMAIN, data=ENTRYDATA_LEGACY)
    entry.add_to_hass(hass)

    config_entries_domain = hass.config_entries.async_entries(DOMAIN)
    assert len(config_entries_domain) == 1
    assert entry is config_entries_domain[0]
    assert not entry.unique_id

    assert await async_setup_component(hass, DOMAIN, {}) is True
    await hass.async_block_till_done()

    # failed as already configured
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == RESULT_ALREADY_CONFIGURED

    config_entries_domain = hass.config_entries.async_entries(DOMAIN)
    assert len(config_entries_domain) == 1
    entry2 = config_entries_domain[0]

    # check updated device info
    assert entry2.unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"