async def test_get_execution_diagnostics_full():
    """Test get_execution_diagnostics aggregates all data correctly."""
    mock_row = {
        "running_count": 10,
        "queued_db_count": 5,
        "orphaned_running": 2,
        "orphaned_queued": 1,
        "failed_count_1h": 3,
        "failed_count_24h": 12,
        "stuck_running_24h": 1,
        "stuck_running_1h": 2,
        "stuck_queued_1h": 4,
        "queued_never_started": 3,
        "invalid_queued_with_start": 1,
        "invalid_running_without_start": 0,
        "completed_1h": 50,
        "completed_24h": 600,
    }

    mock_exec = MagicMock()
    mock_exec.started_at = datetime.now(timezone.utc) - timedelta(hours=48)

    with (
        patch(
            "backend.data.diagnostics.query_raw_with_schema",
            new_callable=AsyncMock,
            return_value=[mock_row],
        ),
        patch(
            "backend.data.diagnostics.get_rabbitmq_queue_depth",
            return_value=7,
        ),
        patch(
            "backend.data.diagnostics.get_rabbitmq_cancel_queue_depth",
            return_value=2,
        ),
        patch(
            "backend.data.diagnostics.get_graph_executions",
            new_callable=AsyncMock,
            return_value=[mock_exec],
        ),
    ):
        result = await get_execution_diagnostics()

    assert result.running_count == 10
    assert result.queued_db_count == 5
    assert result.orphaned_running == 2
    assert result.orphaned_queued == 1
    assert result.failed_count_1h == 3
    assert result.failed_count_24h == 12
    assert result.failure_rate_24h == 12 / 24.0
    assert result.stuck_running_24h == 1
    assert result.stuck_running_1h == 2
    assert result.stuck_queued_1h == 4
    assert result.queued_never_started == 3
    assert result.invalid_queued_with_start == 1
    assert result.invalid_running_without_start == 0
    assert result.completed_1h == 50
    assert result.completed_24h == 600
    assert result.throughput_per_hour == 600 / 24.0
    assert result.rabbitmq_queue_depth == 7
    assert result.cancel_queue_depth == 2
    assert result.oldest_running_hours is not None
    assert result.oldest_running_hours > 47.0