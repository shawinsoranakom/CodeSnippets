async def test_start_end_tracers(tracing_service):
    """Test starting and ending tracers."""
    run_id = uuid.uuid4()
    run_name = "test_run"
    user_id = "test_user"
    session_id = "test_session"
    project_name = "test_project"
    outputs = {"output_key": "output_value"}

    await tracing_service.start_tracers(run_id, run_name, user_id, session_id, project_name)
    # Verify trace_context is set correctly
    trace_context = trace_context_var.get()
    assert trace_context is not None
    assert trace_context.run_id == run_id
    assert trace_context.run_name == run_name
    assert trace_context.project_name == project_name
    assert trace_context.user_id == user_id
    assert trace_context.session_id == session_id

    # Verify tracers are initialized
    assert "langsmith" in trace_context.tracers
    assert "langwatch" in trace_context.tracers
    assert "langfuse" in trace_context.tracers
    assert "arize_phoenix" in trace_context.tracers
    assert "opik" in trace_context.tracers
    assert "traceloop" in trace_context.tracers
    assert "native" in trace_context.tracers
    assert "openlayer" in trace_context.tracers

    await tracing_service.end_tracers(outputs)

    # Verify end method was called for all tracers
    trace_context = trace_context_var.get()
    for tracer in trace_context.tracers.values():
        assert tracer.end_called
        assert tracer.metadata_param == outputs
        assert tracer.outputs_param == trace_context.all_outputs

    # Verify worker_task is cancelled
    assert trace_context.worker_task is None
    assert not trace_context.running