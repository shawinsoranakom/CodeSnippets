def _mock_draft_token_ids(
    scheduler_output: SchedulerOutput,
    num_output_tokens_range: tuple[int, int],
    seen_request_prompt_length: dict[str, int],
) -> DraftTokenIds:
    request_ids: list[str] = []
    sampled_token_ids: list[list[int]] = []
    for request in scheduler_output.scheduled_new_reqs:
        assert request.req_id not in seen_request_prompt_length
        seen_request_prompt_length[request.req_id] = len(request.prompt_token_ids or [])
        if request.num_computed_tokens >= seen_request_prompt_length[request.req_id]:
            num_tokens = random.randint(*num_output_tokens_range)
            request_ids.append(request.req_id)
            sampled_token_ids.append(
                [random.randint(0, 100) for _ in range(num_tokens)]
            )
    for req_id, num_computed_tokens in zip(
        scheduler_output.scheduled_cached_reqs.req_ids,
        scheduler_output.scheduled_cached_reqs.num_computed_tokens,
    ):
        if num_computed_tokens >= seen_request_prompt_length[req_id]:
            num_tokens = random.randint(*num_output_tokens_range)
            request_ids.append(req_id)
            sampled_token_ids.append(
                [random.randint(0, 100) for _ in range(num_tokens)]
            )
    return DraftTokenIds(req_ids=request_ids, draft_token_ids=sampled_token_ids)