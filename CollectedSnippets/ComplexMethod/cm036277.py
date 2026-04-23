def test_priority_scheduling_blast(
    enable_prefix_caching: bool,
    num_speculative_tokens: int | None,
    max_input_tokens: int,
    max_output_tokens: int,
    max_num_seqs: int,
    num_blocks: int,
):
    random.seed(42)
    seen_request_prompt_length = dict[str, int]()
    seen_request_ids = set[str]()
    seen_mm_hashes = set[str]()

    scheduler = create_scheduler_with_priority(
        model="Qwen/Qwen2.5-VL-3B-Instruct",
        max_num_seqs=max_num_seqs,
        enable_prefix_caching=enable_prefix_caching,
        num_blocks=num_blocks,
        num_speculative_tokens=num_speculative_tokens,
    )

    num_initial_requests = 10
    for _ in range(num_initial_requests):
        req = _create_random_request(
            max_tokens_range=(1, max_output_tokens),
            num_tokens_range=(1, max_input_tokens),
            arrival_time_range=(0, 1),
            priority_range=(-3, 3),
            num_mm_item_range=(0, 2),
            vllm_config=scheduler.vllm_config,
        )
        scheduler.add_request(req)
    num_initial_requests = 2
    for _ in range(num_initial_requests):
        req = _create_random_request(
            max_tokens_range=(1, max_output_tokens),
            num_tokens_range=(1, max_input_tokens),
            arrival_time_range=(0, 0),
            priority_range=(4, 4),
            num_mm_item_range=(0, 2),
            vllm_config=scheduler.vllm_config,
        )
        scheduler.add_request(req)
    for _ in range(20000):
        if len(scheduler.waiting) == 0:
            num_new_requests = random.randint(0, 2)
            for _ in range(num_new_requests):
                req = _create_random_request(
                    max_tokens_range=(1, max_output_tokens),
                    num_tokens_range=(1, max_input_tokens),
                    arrival_time_range=(0, 1),
                    priority_range=(-3, 3),
                    num_mm_item_range=(0, 2),
                    vllm_config=scheduler.vllm_config,
                )
                scheduler.add_request(req)
        scheduler_output = scheduler.schedule()
        _check_valid_scheduler_output(
            scheduler_output, seen_request_ids, seen_mm_hashes
        )
        model_output = _mock_execute_model(
            scheduler_output,
            num_output_tokens_range=(1, 1 + (num_speculative_tokens or 0)),
        )
        scheduler.update_from_output(scheduler_output, model_output)
        if num_speculative_tokens is not None:
            scheduler.update_draft_token_ids(
                _mock_draft_token_ids(
                    scheduler_output,
                    (0, num_speculative_tokens),
                    seen_request_prompt_length,
                )
            )