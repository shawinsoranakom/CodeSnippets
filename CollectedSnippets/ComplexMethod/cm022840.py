async def test_coordinator_update_after_reboot(
    hass: HomeAssistant, fritz: Mock
) -> None:
    """Test coordinator after reboot."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG[DOMAIN][CONF_DEVICES][0],
        unique_id="any",
    )
    entry.add_to_hass(hass)
    fritz().update_devices.side_effect = ["", HTTPError()]

    assert await hass.config_entries.async_setup(entry.entry_id)
    assert fritz().update_devices.call_count == 1
    assert fritz().update_templates.call_count == 1
    assert fritz().get_devices.call_count == 1
    assert fritz().get_templates.call_count == 1
    assert fritz().login.call_count == 1

    async_fire_time_changed(hass, utcnow() + timedelta(seconds=35))
    await hass.async_block_till_done(wait_background_tasks=True)

    assert entry.state is ConfigEntryState.SETUP_RETRY