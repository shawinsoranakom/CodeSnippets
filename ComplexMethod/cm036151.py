def test_sampler_repetition_penalty(
    device: str, batch_size: int, repetition_penalty: float
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
    sampling_metadata.repetition_penalties = _create_penalty_tensor(
        batch_size, repetition_penalty, torch.device(device)
    )
    sampling_metadata.no_penalties = False
    sampler = Sampler()
    logits = sampler.apply_penalties(
        fake_logits, sampling_metadata, sampling_metadata.output_token_ids
    )
    logits = logits.cpu()
    for batch_idx in range(batch_size):
        non_penalized_token_id = logits[batch_idx].argmax().item()
        penalized_token_id = logits[batch_idx].argmin().item()
        prompt_tokens = sampling_metadata.prompt_token_ids[batch_idx][:].tolist()
        output_tokens = sampling_metadata.output_token_ids[batch_idx]
        if repetition_penalty > 1.0:
            # If `repetition_penalty` > 1.0, verify that the non-penalized
            # token ID has not been seen before, while the penalized token ID
            # exists either in the prompt or the output.
            assert (
                non_penalized_token_id not in prompt_tokens
                and non_penalized_token_id not in output_tokens
            )
            assert (
                penalized_token_id in prompt_tokens
                or penalized_token_id in output_tokens
            )
        elif repetition_penalty < 1.0:
            # If `repetition_penalty` < 1.0, verify that the penalized
            # token ID has not been seen before, while the non-penalized
            # token ID exists either in the prompt or the output.
            assert (
                penalized_token_id not in prompt_tokens
                and penalized_token_id not in output_tokens
            )
            assert (
                non_penalized_token_id in prompt_tokens
                or non_penalized_token_id in output_tokens
            )