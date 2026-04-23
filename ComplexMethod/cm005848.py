async def test_trace_component(tracing_service, mock_component):
    """Test component tracing context manager."""
    run_id = uuid.uuid4()
    run_name = "test_run"
    user_id = "test_user"
    session_id = "test_session"
    project_name = "test_project"

    trace_name = "test_component_trace"
    inputs = {"input_key": "input_value"}
    metadata = {"metadata_key": "metadata_value"}

    await tracing_service.start_tracers(run_id, run_name, user_id, session_id, project_name)

    async with tracing_service.trace_component(mock_component, trace_name, inputs, metadata) as ts:
        # Verify component context is set
        component_context = component_context_var.get()
        assert component_context is not None
        assert component_context.trace_id == mock_component._vertex.id
        assert component_context.trace_name == trace_name
        assert component_context.trace_type == mock_component.trace_type
        assert component_context.vertex == mock_component._vertex
        assert component_context.inputs == inputs
        assert component_context.inputs_metadata == metadata

        # Verify add_trace method was called for tracers
        await asyncio.sleep(0.1)  # Wait for async queue processing
        trace_context = trace_context_var.get()
        for tracer in trace_context.tracers.values():
            assert tracer.add_trace_list[0]["trace_id"] == mock_component._vertex.id
            assert tracer.add_trace_list[0]["trace_name"] == trace_name
            assert tracer.add_trace_list[0]["trace_type"] == mock_component.trace_type
            assert tracer.add_trace_list[0]["inputs"] == inputs
            assert tracer.add_trace_list[0]["metadata"] == metadata
            assert tracer.add_trace_list[0]["vertex"] == mock_component._vertex

        # Test adding logs
        ts.add_log(trace_name, {"message": "test log"})
        assert {"message": "test log"} in component_context.logs[trace_name]

        # Test setting outputs
        outputs = {"output_key": "output_value"}
        output_metadata = {"output_metadata_key": "output_metadata_value"}
        ts.set_outputs(trace_name, outputs, output_metadata)
        assert component_context.outputs[trace_name] == outputs
        assert component_context.outputs_metadata[trace_name] == output_metadata
        assert trace_context.all_outputs[trace_name] == outputs

    # Verify end_trace method was called for tracers
    await asyncio.sleep(0.1)  # Wait for async queue processing
    for tracer in trace_context.tracers.values():
        assert tracer.end_trace_list[0]["trace_id"] == mock_component._vertex.id
        assert tracer.end_trace_list[0]["trace_name"] == trace_name
        assert tracer.end_trace_list[0]["outputs"] == trace_context.all_outputs[trace_name]
        assert tracer.end_trace_list[0]["error"] is None
        assert tracer.end_trace_list[0]["logs"] == component_context.logs[trace_name]

    # Cleanup
    await tracing_service.end_tracers({})