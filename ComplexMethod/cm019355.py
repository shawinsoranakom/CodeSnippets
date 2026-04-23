async def test_duplicate_config_entries(
    hass: HomeAssistant,
    mock_code_flow: Mock,
    mock_exchange: Mock,
    config_entry: MockConfigEntry,
) -> None:
    """Test that the same account cannot be setup twice."""
    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET)
    )

    # Load a config entry
    config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.google.async_setup_entry", return_value=True
    ) as mock_setup:
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        assert len(mock_setup.mock_calls) == 1

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    # Start a new config flow using the same credential
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.SHOW_PROGRESS
    assert result.get("step_id") == "auth"
    assert "description_placeholders" in result
    assert "url" in result["description_placeholders"]

    # Run one tick to invoke the credential exchange check
    now = utcnow()
    await fire_alarm(hass, now + CODE_CHECK_ALARM_TIMEDELTA)
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(flow_id=result["flow_id"])
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "already_configured"