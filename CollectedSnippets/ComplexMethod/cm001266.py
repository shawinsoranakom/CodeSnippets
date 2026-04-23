def test_stop_single_execution_with_stop_graph_execution(
    mocker: pytest_mock.MockFixture,
    admin_user_id: str,
):
    """Test stopping uses robust stop_graph_execution"""
    mock_exec_meta = GraphExecutionMeta(
        id="exec-running-123",
        user_id="user-789",
        graph_id="graph-999",
        graph_version=2,
        inputs=None,
        credential_inputs=None,
        nodes_input_masks=None,
        preset_id=None,
        status=AgentExecutionStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
        ended_at=datetime.now(timezone.utc),
        stats=None,
    )

    mocker.patch(
        "backend.api.features.admin.diagnostics_admin_routes.get_graph_executions",
        return_value=[mock_exec_meta],
    )

    mock_stop_graph_execution = mocker.patch(
        "backend.api.features.admin.diagnostics_admin_routes.stop_graph_execution",
        return_value=AsyncMock(),
    )

    response = client.post(
        "/admin/diagnostics/executions/stop",
        json={"execution_id": "exec-running-123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["stopped_count"] == 1

    # Verify it used stop_graph_execution with cascade
    mock_stop_graph_execution.assert_called_once()
    call_kwargs = mock_stop_graph_execution.call_args.kwargs
    assert call_kwargs["graph_exec_id"] == "exec-running-123"
    assert call_kwargs["user_id"] == "user-789"
    assert call_kwargs["cascade"] is True  # Stops children too!
    assert call_kwargs["wait_timeout"] == 15.0