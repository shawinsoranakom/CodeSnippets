def _step_until_kv_transfer_finished(scheduler: Scheduler, req_ids: list[str]):
    """Cycle requests through a KV transfer cycle."""

    # Requests should first transition to WAITING_FOR_REMOTE_KVS
    output = scheduler.schedule()
    assert _num_waiting_requests(scheduler) == len(req_ids)
    assert len(scheduler.running) == 0
    assert len(output.scheduled_new_reqs) == 0
    for req in scheduler.requests.values():
        assert req.status == RequestStatus.WAITING_FOR_REMOTE_KVS

    # No model execution yet
    EMPTY_OUTPUT = ModelRunnerOutput(
        req_ids=[],
        req_id_to_index={},
        sampled_token_ids=[],
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    initial_ecos = scheduler.update_from_output(output, EMPTY_OUTPUT)

    # Simulate KV transfer completion using KVConnectorOutput.finished_recving
    output = scheduler.schedule()
    assert _num_waiting_requests(scheduler) == len(req_ids)
    assert len(scheduler.running) == 0

    MODEL_RUNNER_OUTPUT = ModelRunnerOutput(
        req_ids=[],
        req_id_to_index={},
        sampled_token_ids=[],
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
        kv_connector_output=KVConnectorOutput(finished_recving=req_ids),
    )
    scheduler.update_from_output(output, MODEL_RUNNER_OUTPUT)
    for req_id in req_ids:
        assert req_id in scheduler.finished_recving_kv_req_ids

    return initial_ecos