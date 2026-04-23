async def test_get_execution_diagnostics_empty_db():
    """Test get_execution_diagnostics with empty database."""
    with (
        patch(
            "backend.data.diagnostics.query_raw_with_schema",
            new_callable=AsyncMock,
            return_value=[{}],
        ),
        patch(
            "backend.data.diagnostics.get_rabbitmq_queue_depth",
            return_value=-1,
        ),
        patch(
            "backend.data.diagnostics.get_rabbitmq_cancel_queue_depth",
            return_value=-1,
        ),
        patch(
            "backend.data.diagnostics.get_graph_executions",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        result = await get_execution_diagnostics()

    assert result.running_count == 0
    assert result.queued_db_count == 0
    assert result.failure_rate_24h == 0.0
    assert result.throughput_per_hour == 0.0
    assert result.oldest_running_hours is None
    assert result.rabbitmq_queue_depth == -1
    assert result.cancel_queue_depth == -1