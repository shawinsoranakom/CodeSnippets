def test_sampler_presence_penalty(
    device: str, batch_size: int, presence_penalty: float
):
    """
    Test to verify that if presence penalty is enabled then tokens
    are penalized as per their presence in the existing output.
    """
    torch.set_default_device(device)
    # Create fake logits where each token is assigned the same
    # logit value.
    fake_logits = _create_fake_logits(batch_size, VOCAB_SIZE)
    sampling_metadata = _create_default_sampling_metadata(
        NUM_OUTPUT_TOKENS, batch_size, VOCAB_SIZE, torch.device(device)
    )
    output_token_ids = sampling_metadata.output_token_ids
    sampling_metadata.presence_penalties = _create_penalty_tensor(
        batch_size, presence_penalty, torch.device(device)
    )
    sampling_metadata.no_penalties = False
    sampler = Sampler()
    logits = sampler.apply_penalties(
        fake_logits, sampling_metadata, sampling_metadata.output_token_ids
    )
    logits = logits.cpu()
    for batch_idx in range(batch_size):
        # Since all tokens initially have the same logits, the non-penalized
        # token ID will be the one with the highest logit value, while the
        # penalized token ID will be the one with the lowest logit value.
        non_penalized_token_id = logits[batch_idx].argmax().item()
        penalized_token_id = logits[batch_idx].argmin().item()
        if presence_penalty > 0:
            # If `presence_penalty` is set to a value greater than 0, it
            # indicates a preference for new tokens over those already
            # present in the output.
            # Verify that the penalized token ID exists in the output, while the
            # non-penalized token ID does not.
            assert penalized_token_id in output_token_ids[batch_idx]
            assert non_penalized_token_id not in output_token_ids[batch_idx]
        elif presence_penalty < 0:
            # If `presence_penalty` is set to a value less than 0, it indicates
            # a preference for existing tokens over new ones. Verify that the
            # non-penalized token ID exists in the output, while the penalized
            # token ID does not.
            assert non_penalized_token_id in output_token_ids[batch_idx]
            assert penalized_token_id not in output_token_ids[batch_idx]