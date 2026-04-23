def create_sampling_metadata(
    all_greedy: bool,
    output_token_ids: list[list[int]] | None = None,
    prompt_token_ids: torch.Tensor | None = None,
    spec_token_ids: torch.Tensor | None = None,
    temperature: torch.Tensor | None = None,
    top_k: torch.Tensor | None = None,
    top_p: torch.Tensor | None = None,
    generators: dict[int, Any] | None = None,
    frequency_penalties: list[float] | None = None,
    presence_penalties: list[float] | None = None,
    repetition_penalties: list[float] | None = None,
    bad_words_token_ids: dict[int, list[list[int]]] | None = None,
    allowed_token_ids_mask: torch.Tensor | None = None,
) -> SamplingMetadata:
    """Create a v1 sampling metadata object with all_greedy set
    to the given value. Either all greedy or all random sampling
    is used.
    """
    generators = generators or {}
    if all_greedy:
        temperature = None
    else:
        assert temperature is not None

    if any([frequency_penalties, presence_penalties, repetition_penalties]):
        no_penalties = False

        assert output_token_ids
        assert len(output_token_ids) > 0

        frequency_penalties = torch.tensor(frequency_penalties, device=DEVICE_TYPE)
        presence_penalties = torch.tensor(presence_penalties, device=DEVICE_TYPE)
        repetition_penalties = torch.tensor(repetition_penalties, device=DEVICE_TYPE)
    else:
        no_penalties = True
        frequency_penalties = torch.tensor([])
        presence_penalties = torch.tensor([])
        repetition_penalties = torch.tensor([])

    return SamplingMetadata(
        temperature=temperature,
        all_greedy=all_greedy,
        all_random=not all_greedy,
        top_p=top_p,
        top_k=top_k,
        generators=generators,
        max_num_logprobs=None,
        no_penalties=no_penalties,
        prompt_token_ids=prompt_token_ids,
        frequency_penalties=frequency_penalties,
        presence_penalties=presence_penalties,
        repetition_penalties=repetition_penalties,
        output_token_ids=[] if output_token_ids is None else output_token_ids,
        spec_token_ids=[] if spec_token_ids is None else spec_token_ids,
        allowed_token_ids_mask=allowed_token_ids_mask,
        bad_words_token_ids={} if bad_words_token_ids is None else bad_words_token_ids,
        logitsprocs=LogitsProcessors(),
    )