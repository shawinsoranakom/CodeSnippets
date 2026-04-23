async def test_execute_stmt_lambda_element(
    hass: HomeAssistant,
    setup_recorder: None,
) -> None:
    """Test executing with execute_stmt_lambda_element."""
    instance = recorder.get_instance(hass)
    hass.states.async_set("sensor.on", "on")
    new_state = hass.states.get("sensor.on")
    await async_wait_recording_done(hass)
    now = dt_util.utcnow()
    tomorrow = now + timedelta(days=1)
    one_week_from_now = now + timedelta(days=7)
    all_calls = 0

    class MockExecutor:
        def __init__(self, stmt) -> None:
            assert isinstance(stmt, StatementLambdaElement)

        def all(self):
            nonlocal all_calls
            all_calls += 1
            if all_calls == 2:
                return ["mock_row"]
            raise SQLAlchemyError

    with session_scope(hass=hass) as session:
        # No time window, we always get a list
        metadata_id = instance.states_meta_manager.get("sensor.on", session, True)
        start_time_ts = dt_util.utcnow().timestamp()
        stmt = lambda_stmt(
            lambda: _get_single_entity_start_time_stmt(
                start_time_ts, metadata_id, False, False, False
            )
        )
        rows = util.execute_stmt_lambda_element(session, stmt)
        assert isinstance(rows, list)
        assert rows[0].state == new_state.state
        assert rows[0].metadata_id == metadata_id

        # Time window >= 2 days, we get a ChunkedIteratorResult
        rows = util.execute_stmt_lambda_element(session, stmt, now, one_week_from_now)
        assert isinstance(rows, ChunkedIteratorResult)
        row = next(rows)
        assert row.state == new_state.state
        assert row.metadata_id == metadata_id

        # Time window >= 2 days, we should not get a ChunkedIteratorResult
        # because orm_rows=False
        rows = util.execute_stmt_lambda_element(
            session, stmt, now, one_week_from_now, orm_rows=False
        )
        assert not isinstance(rows, ChunkedIteratorResult)
        row = next(rows)
        assert row.state == new_state.state
        assert row.metadata_id == metadata_id

        # Time window < 2 days, we get a list
        rows = util.execute_stmt_lambda_element(session, stmt, now, tomorrow)
        assert isinstance(rows, list)
        assert rows[0].state == new_state.state
        assert rows[0].metadata_id == metadata_id

        with patch.object(session, "execute", MockExecutor):
            rows = util.execute_stmt_lambda_element(session, stmt, now, tomorrow)
            assert rows == ["mock_row"]