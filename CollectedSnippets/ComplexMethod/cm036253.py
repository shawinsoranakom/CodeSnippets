def _step_until_done(
    scheduler: Scheduler,
    output: SchedulerOutput,
    model_runner_output: ModelRunnerOutput,
):
    """Loop over schedule(), update_from_output() until finished."""

    all_finished = False
    _ = scheduler.update_from_output(output, model_runner_output)
    while not all_finished:
        # Schedule + a few iterations until stopping.
        output = scheduler.schedule()
        assert len(scheduler.running)
        for _, num_scheduled_tokens in output.num_scheduled_tokens.items():
            # We should be in the decode phase now.
            assert num_scheduled_tokens == 1
        if scheduler.connector is not None:
            assert len(output.kv_connector_metadata.requests) == 0
        if scheduler.ec_connector is not None:
            assert len(output.ec_connector_metadata.mm_datas) == 0
        ecos = scheduler.update_from_output(output, model_runner_output)[0]
        all_done = True
        for eco in ecos.outputs:
            if eco.finish_reason is None:
                all_done = False
        all_finished = all_done