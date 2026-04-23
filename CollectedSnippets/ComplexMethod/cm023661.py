async def test_import_statistics_with_error(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
    unit_class: str,
    unit: str,
    error_message: str,
    source,
    statistic_id,
) -> None:
    """Test importing statistics."""
    client = await hass_ws_client()

    assert "Compiling statistics for" not in caplog.text
    assert "Statistics already compiled" not in caplog.text

    zero = dt_util.utcnow()
    period1 = zero.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    period2 = zero.replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)

    imported_statistics1 = {
        "start": period1.isoformat(),
        "last_reset": None,
        "state": 0,
        "sum": 2,
    }
    imported_statistics2 = {
        "start": period2.isoformat(),
        "last_reset": None,
        "state": 1,
        "sum": 3,
    }

    imported_metadata = {
        "has_sum": True,
        "mean_type": int(StatisticMeanType.NONE),
        "name": "Total imported energy",
        "source": source,
        "statistic_id": statistic_id,
        "unit_class": unit_class,
        "unit_of_measurement": unit,
    }

    await client.send_json_auto_id(
        {
            "type": "recorder/import_statistics",
            "metadata": imported_metadata,
            "stats": [imported_statistics1, imported_statistics2],
        }
    )
    response = await client.receive_json()
    assert not response["success"]
    assert response["error"] == {
        "code": "home_assistant_error",
        "message": error_message,
    }

    await async_wait_recording_done(hass)
    stats = statistics_during_period(
        hass, zero, period="hour", statistic_ids={statistic_id}
    )
    assert stats == {}
    statistic_ids = list_statistic_ids(hass)
    assert statistic_ids == []
    metadata = get_metadata(hass, statistic_ids={statistic_id})
    assert metadata == {}
    last_stats = get_last_statistics(
        hass,
        1,
        statistic_id,
        True,
        {"last_reset", "max", "mean", "min", "state", "sum"},
    )
    assert last_stats == {}