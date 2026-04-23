async def test_reconfigure_flow_api_key(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    solaredge_api: Mock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test reconfigure flow with API key."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=NAME,
        data={CONF_SITE_ID: SITE_ID, CONF_API_KEY: "old_api_key"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SECTION_API_AUTH: {CONF_API_KEY: API_KEY},
        },
    )
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reconfigure_successful"

    await hass.async_block_till_done()

    assert entry.title == NAME
    assert entry.data[CONF_SITE_ID] == SITE_ID
    assert entry.data[CONF_API_KEY] == API_KEY
    assert mock_setup_entry.call_count == 1