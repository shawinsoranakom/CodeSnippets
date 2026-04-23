async def test_remove(
    hass: HomeAssistant,
    ista_config_entry: MockConfigEntry,
) -> None:
    """Test remove config entry and clear statistics."""
    ista_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(ista_config_entry.entry_id)
    await hass.async_block_till_done()

    assert ista_config_entry.state is ConfigEntryState.LOADED
    await async_wait_recording_done(hass)

    assert await hass.async_add_executor_job(
        statistics_during_period,
        hass,
        datetime.datetime.fromtimestamp(0, tz=datetime.UTC),
        None,
        {"ista_ecotrend:bahnhofsstr_1a_heating"},
        "month",
        None,
        {"state", "sum"},
    )

    assert await hass.config_entries.async_unload(ista_config_entry.entry_id)
    await hass.async_block_till_done()

    assert ista_config_entry.state is ConfigEntryState.NOT_LOADED
    await async_wait_recording_done(hass)

    assert await hass.async_add_executor_job(
        statistics_during_period,
        hass,
        datetime.datetime.fromtimestamp(0, tz=datetime.UTC),
        None,
        {"ista_ecotrend:bahnhofsstr_1a_heating"},
        "month",
        None,
        {"state", "sum"},
    )

    assert await hass.config_entries.async_remove(ista_config_entry.entry_id)
    await hass.async_block_till_done()

    await async_wait_recording_done(hass)

    assert not await hass.async_add_executor_job(
        statistics_during_period,
        hass,
        datetime.datetime.fromtimestamp(0, tz=datetime.UTC),
        None,
        {"ista_ecotrend:bahnhofsstr_1a_heating"},
        "month",
        None,
        {"state", "sum"},
    )