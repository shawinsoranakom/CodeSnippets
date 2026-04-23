async def test_integration_update_interval(
    hass: HomeAssistant,
    cfupdate: MagicMock,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test integration update interval."""
    instance = cfupdate.return_value

    entry = await init_integration(hass)
    assert entry.state is ConfigEntryState.LOADED

    freezer.tick(timedelta(minutes=DEFAULT_UPDATE_INTERVAL))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(instance.list_dns_records.mock_calls) == 2
    assert len(instance.update_dns_record.mock_calls) == 4
    assert "All target records are up to date" not in caplog.text

    instance.list_dns_records.side_effect = pycfdns.AuthenticationException()
    freezer.tick(timedelta(minutes=DEFAULT_UPDATE_INTERVAL))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(instance.list_dns_records.mock_calls) == 3
    assert len(instance.update_dns_record.mock_calls) == 4

    instance.list_dns_records.side_effect = pycfdns.ComunicationException()
    freezer.tick(timedelta(minutes=DEFAULT_UPDATE_INTERVAL))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert len(instance.list_dns_records.mock_calls) == 4
    assert len(instance.update_dns_record.mock_calls) == 4