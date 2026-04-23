async def test_external_statistics_errors(
    hass: HomeAssistant, setup_recorder: None, caplog: pytest.LogCaptureFixture
) -> None:
    """Test validation of external statistics."""
    await async_wait_recording_done(hass)
    assert "Compiling statistics for" not in caplog.text
    assert "Statistics already compiled" not in caplog.text

    zero = dt_util.utcnow()
    last_reset = zero.replace(minute=0, second=0, microsecond=0) - timedelta(days=1)
    period1 = zero.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    _external_statistics = {
        "start": period1,
        "last_reset": last_reset,
        "state": 0,
        "sum": 2,
    }

    _external_metadata = {
        "has_sum": True,
        "mean_type": StatisticMeanType.NONE,
        "name": "Total imported energy",
        "source": "test",
        "statistic_id": "test:total_energy_import",
        "unit_class": "energy",
        "unit_of_measurement": "kWh",
    }

    # Attempt to insert statistics for an entity
    external_metadata = {
        **_external_metadata,
        "statistic_id": "sensor.total_energy_import",
    }
    external_statistics = {**_external_statistics}
    with pytest.raises(HomeAssistantError):
        async_add_external_statistics(hass, external_metadata, (external_statistics,))
    await async_wait_recording_done(hass)
    assert statistics_during_period(hass, zero, period="hour") == {}
    assert list_statistic_ids(hass) == []
    assert get_metadata(hass, statistic_ids={"sensor.total_energy_import"}) == {}

    # Attempt to insert statistics for the wrong domain
    external_metadata = {**_external_metadata, "source": "other"}
    external_statistics = {**_external_statistics}
    with pytest.raises(HomeAssistantError):
        async_add_external_statistics(hass, external_metadata, (external_statistics,))
    await async_wait_recording_done(hass)
    assert statistics_during_period(hass, zero, period="hour") == {}
    assert list_statistic_ids(hass) == []
    assert get_metadata(hass, statistic_ids={"test:total_energy_import"}) == {}

    # Attempt to insert statistics for a naive starting time
    external_metadata = {**_external_metadata}
    external_statistics = {
        **_external_statistics,
        "start": period1.replace(tzinfo=None),
    }
    with pytest.raises(HomeAssistantError):
        async_add_external_statistics(hass, external_metadata, (external_statistics,))
    await async_wait_recording_done(hass)
    assert statistics_during_period(hass, zero, period="hour") == {}
    assert list_statistic_ids(hass) == []
    assert get_metadata(hass, statistic_ids={"test:total_energy_import"}) == {}

    # Attempt to insert statistics for an invalid starting time
    external_metadata = {**_external_metadata}
    external_statistics = {**_external_statistics, "start": period1.replace(minute=1)}
    with pytest.raises(HomeAssistantError):
        async_add_external_statistics(hass, external_metadata, (external_statistics,))
    await async_wait_recording_done(hass)
    assert statistics_during_period(hass, zero, period="hour") == {}
    assert list_statistic_ids(hass) == []
    assert get_metadata(hass, statistic_ids={"test:total_energy_import"}) == {}

    # Attempt to insert statistics with a naive last_reset
    external_metadata = {**_external_metadata}
    external_statistics = {
        **_external_statistics,
        "last_reset": last_reset.replace(tzinfo=None),
    }
    with pytest.raises(HomeAssistantError):
        async_add_external_statistics(hass, external_metadata, (external_statistics,))
    await async_wait_recording_done(hass)
    assert statistics_during_period(hass, zero, period="hour") == {}
    assert list_statistic_ids(hass) == []
    assert get_metadata(hass, statistic_ids={"test:total_energy_import"}) == {}