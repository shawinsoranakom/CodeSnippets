async def test_query_recover_from_rollback(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the SQL sensor."""
    options = {
        CONF_QUERY: "SELECT 5 as value",
        CONF_COLUMN_NAME: "value",
        CONF_UNIQUE_ID: "very_unique_id",
    }
    await init_integration(hass, title="Select value SQL query", options=options)

    state = hass.states.get("sensor.select_value_sql_query")
    assert state.state == "5"
    assert state.attributes["value"] == 5

    with patch(
        "homeassistant.components.sql.sensor.generate_lambda_stmt",
        return_value=generate_lambda_stmt("Faulty syntax create operational issue"),
    ):
        freezer.tick(timedelta(minutes=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert "sqlite3.OperationalError" in caplog.text

    state = hass.states.get("sensor.select_value_sql_query")
    assert state.state == "5"
    assert state.attributes.get("value") is None

    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("sensor.select_value_sql_query")
    assert state.state == "5"
    assert state.attributes.get("value") == 5