def _construct_expected_sampling_metadata(
    reqs: list[CachedRequestState],
    req_ids_retained: set[int],
    req_id_index_in_input_batch: dict[str, int],
    device: torch.device,
) -> SamplingMetadata:
    """
    Constructs and returns the expected SamplingMetadata for this
    batch.
    """
    num_reqs = len(req_ids_retained)
    output_token_ids: list[list[int]] = [list() for _ in range(num_reqs)]
    prompt_token_ids: list[list[int]] = [list() for _ in range(num_reqs)]
    presence_penalties = [0.0 for _ in range(num_reqs)]
    frequency_penalties = [0.0 for _ in range(num_reqs)]
    repetition_penalties = [1.0 for _ in range(num_reqs)]
    top_k = [0 for _ in range(num_reqs)]
    top_p = [0.0 for _ in range(num_reqs)]
    temperature = [0.0 for _ in range(num_reqs)]
    min_tokens = {}
    logit_bias = [None] * num_reqs
    allowed_token_ids_mask = torch.zeros(
        num_reqs, VOCAB_SIZE, dtype=torch.bool, device=device
    )
    bad_words_token_ids = {}
    for req in reqs:
        if req.req_id not in req_ids_retained:
            continue
        index_in_input_batch = req_id_index_in_input_batch[req.req_id]
        output_token_ids[index_in_input_batch] = req.output_token_ids
        prompt_token_ids[index_in_input_batch] = req.prompt_token_ids
        presence_penalties[index_in_input_batch] = req.sampling_params.presence_penalty
        frequency_penalties[index_in_input_batch] = (
            req.sampling_params.frequency_penalty
        )
        repetition_penalties[index_in_input_batch] = (
            req.sampling_params.repetition_penalty
        )
        top_k[index_in_input_batch] = req.sampling_params.top_k
        top_p[index_in_input_batch] = req.sampling_params.top_p
        temperature[index_in_input_batch] = req.sampling_params.temperature
        min_tokens[index_in_input_batch] = (
            req.sampling_params.min_tokens,
            req.sampling_params.all_stop_token_ids,
        )
        logit_bias[index_in_input_batch] = req.sampling_params.logit_bias
        if req.sampling_params.allowed_token_ids:
            allowed_token_ids_mask[index_in_input_batch][
                req.sampling_params.allowed_token_ids
            ] = True
        if req.sampling_params.bad_words_token_ids:
            bad_words_token_ids[index_in_input_batch] = (
                req.sampling_params.bad_words_token_ids
            )

    return SamplingMetadata(
        temperature=torch.tensor(temperature, dtype=torch.float, device=device),
        all_greedy=False,
        all_random=True,
        top_p=None
        if all(x == 1.0 for x in top_p)
        else torch.tensor(top_p, dtype=torch.float, device=device),
        top_k=None
        if all(x == 0 for x in top_k)
        else torch.tensor(top_k, dtype=torch.int, device=device),
        generators={},
        max_num_logprobs=0,
        prompt_token_ids=make_tensor_with_pad(
            prompt_token_ids,
            pad=VOCAB_SIZE,
            device=torch.device(device),
            dtype=torch.int64,
        ),
        frequency_penalties=torch.tensor(
            frequency_penalties, dtype=torch.float, device=device
        ),
        presence_penalties=torch.tensor(
            presence_penalties, dtype=torch.float, device=device
        ),
        repetition_penalties=torch.tensor(
            repetition_penalties, dtype=torch.float, device=device
        ),
        output_token_ids=output_token_ids,
        spec_token_ids=[[] for _ in range(len(output_token_ids))],
        no_penalties=(
            all(x == 0 for x in presence_penalties)
            and all(x == 0 for x in frequency_penalties)
            and all(x == 1 for x in repetition_penalties)
        ),
        allowed_token_ids_mask=allowed_token_ids_mask,
        bad_words_token_ids=bad_words_token_ids,
        logitsprocs=LogitsProcessors(),
    )