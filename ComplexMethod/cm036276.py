def _check_valid_scheduler_output(
    scheduler_output: SchedulerOutput,
    seen_request_ids: set[str],
    seen_mm_hashes: set[str],
):
    for req in scheduler_output.scheduled_new_reqs:
        assert req.req_id not in seen_request_ids
        seen_request_ids.add(req.req_id)
    for req_id in scheduler_output.scheduled_cached_reqs.req_ids:
        assert req_id in seen_request_ids

    req_ids = set[str]()
    req_ids.update(req.req_id for req in scheduler_output.scheduled_new_reqs)
    req_ids.update(scheduler_output.scheduled_cached_reqs.req_ids)

    assert set(scheduler_output.num_scheduled_tokens.keys()) == req_ids
    assert (
        sum(scheduler_output.num_scheduled_tokens.values())
        == scheduler_output.total_num_scheduled_tokens
    )

    assert set(scheduler_output.scheduled_spec_decode_tokens.keys()) <= req_ids
    assert set(scheduler_output.scheduled_encoder_inputs.keys()) <= req_ids

    for req in scheduler_output.scheduled_new_reqs:
        for mm_feature in req.mm_features:
            seen_mm_hashes.add(mm_feature.identifier)
    for mm_hash in scheduler_output.free_encoder_mm_hashes:
        assert mm_hash in seen_mm_hashes

    assert scheduler_output.finished_req_ids <= seen_request_ids