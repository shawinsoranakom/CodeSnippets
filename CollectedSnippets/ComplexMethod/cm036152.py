def test_sampler_allowed_token_ids(
    device: str, batch_size: int, num_allowed_token_ids: int
):
    """
    Test to verify that when the repetition penalty is enabled, tokens
    are penalized based on their presence in the prompt or the existing
    output.
    """
    torch.set_default_device(device)
    # Create fake logits where each token is assigned the same
    # logit value.
    fake_logits = _create_fake_logits(batch_size, VOCAB_SIZE)
    sampling_metadata = _create_default_sampling_metadata(
        NUM_OUTPUT_TOKENS, batch_size, VOCAB_SIZE, torch.device(device)
    )
    mask = create_allowed_token_ids(
        batch_size=batch_size,
        vocab_size=VOCAB_SIZE,
        num_allowed_token_ids=num_allowed_token_ids,
        device=device,
    )
    sampling_metadata.allowed_token_ids_mask = mask
    sampler = Sampler()
    logits = sampler.apply_logits_processors(
        fake_logits, sampling_metadata, predict_bonus_token=False
    )
    logits = logits.cpu()
    for batch_idx in range(batch_size):
        logits_for_req = logits[batch_idx]
        if batch_idx % 2 == 1:
            assert torch.all(logits_for_req != -float("inf"))
            continue
        for token_id in range(VOCAB_SIZE):
            start = min(batch_idx, VOCAB_SIZE - 1)
            end = min(batch_idx + num_allowed_token_ids, VOCAB_SIZE - 1)
            if token_id >= start and token_id < end:
                assert logits_for_req[token_id] == -float("inf"), (
                    f"{batch_idx}, {token_id}"
                )
            else:
                assert logits_for_req[token_id] != -float("inf")