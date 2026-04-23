async def test_concurrent_tracing(tracing_service, mock_component):
    """Test two tasks running start_tracers concurrently, with each task running 2 concurrent trace_component tasks."""

    # Define common task function: start tracers and run two component traces
    async def run_task(
        run_id,
        run_name,
        user_id,
        session_id,
        project_name,
        inputs,
        metadata,
        task_prefix,
        sleep_duration=0.1,
    ):
        await tracing_service.start_tracers(run_id, run_name, user_id, session_id, project_name)

        async def run_component_task(component, trace_name, component_suffix):
            async with tracing_service.trace_component(component, trace_name, inputs, metadata) as ts:
                ts.add_log(trace_name, {"message": f"{task_prefix} {component_suffix} log"})
                outputs = {"output_key": f"{task_prefix}_{component_suffix}_output"}
                await asyncio.sleep(sleep_duration)
                ts.set_outputs(trace_name, outputs)

        task1 = asyncio.create_task(run_component_task(mock_component, f"{run_id} trace_name1", f"{run_id} component1"))
        await task1
        task2 = asyncio.create_task(run_component_task(mock_component, f"{run_id} trace_name2", f"{run_id} component2"))
        await task2

        await tracing_service.end_tracers({"final_output": f"{task_prefix}_final_output"})
        trace_context = trace_context_var.get()
        return trace_context.tracers["langfuse"]

    inputs1 = {"input_key": "input_value1"}
    metadata1 = {"metadata_key": "metadata_value1"}
    inputs2 = {"input_key": "input_value2"}
    metadata2 = {"metadata_key": "metadata_value2"}

    task1 = asyncio.create_task(
        run_task(
            "run_id1",
            "run_name1",
            "user_id1",
            "session_id1",
            "project_name1",
            inputs1,
            metadata1,
            "task1",
            2,
        )
    )
    await asyncio.sleep(0.1)
    task2 = asyncio.create_task(
        run_task(
            "run_id2",
            "run_name2",
            "user_id2",
            "session_id2",
            "project_name2",
            inputs2,
            metadata2,
            "task2",
            0.1,
        )
    )
    tracer1 = await task1
    tracer2 = await task2

    # Verify tracer1 and tracer2 have correct trace data
    assert tracer1.trace_name == "run_name1"
    assert tracer1.project_name == "project_name1"
    assert tracer1.user_id == "user_id1"
    assert tracer1.session_id == "session_id1"
    assert dict(tracer1.outputs_param.get("run_id1 trace_name1")) == {"output_key": "task1_run_id1 component1_output"}
    assert dict(tracer1.outputs_param.get("run_id1 trace_name2")) == {"output_key": "task1_run_id1 component2_output"}

    assert tracer2.trace_name == "run_name2"
    assert tracer2.project_name == "project_name2"
    assert tracer2.user_id == "user_id2"
    assert tracer2.session_id == "session_id2"
    assert dict(tracer2.outputs_param.get("run_id2 trace_name1")) == {"output_key": "task2_run_id2 component1_output"}
    assert dict(tracer2.outputs_param.get("run_id2 trace_name2")) == {"output_key": "task2_run_id2 component2_output"}