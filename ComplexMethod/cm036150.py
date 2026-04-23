def test_sampler_frequency_penalty(
    device: str, batch_size: int, frequency_penalty: float
):
    """
    Test to verify that if frequency penalty is enabled then tokens are
    penalized as per their frequency of occurrence.
    """
    torch.set_default_device(device)
    # Create fake logits where each token is assigned the same
    # logit value.
    fake_logits = _create_fake_logits(batch_size, VOCAB_SIZE)
    sampling_metadata = _create_default_sampling_metadata(
        NUM_OUTPUT_TOKENS, batch_size, VOCAB_SIZE, torch.device(device)
    )
    sampling_metadata.frequency_penalties = _create_penalty_tensor(
        batch_size, frequency_penalty, torch.device(device)
    )
    output_token_ids, sorted_token_ids_in_output = _create_weighted_output_token_list(
        batch_size,
        VOCAB_SIZE,
    )
    sampling_metadata.output_token_ids = output_token_ids
    sampling_metadata.no_penalties = False
    sampler = Sampler()
    logits = sampler.apply_penalties(
        fake_logits, sampling_metadata, sampling_metadata.output_token_ids
    )
    logits = logits.cpu()
    for batch_idx in range(batch_size):
        non_penalized_token_id = logits[batch_idx].argmax().item()
        penalized_token_id = logits[batch_idx].argmin().item()
        distinct_sorted_token_ids_in_output = sorted_token_ids_in_output[batch_idx]
        most_frequent_token_id = distinct_sorted_token_ids_in_output[
            len(distinct_sorted_token_ids_in_output) - 1
        ]
        if frequency_penalty > 0:
            # If `frequency_penalty` is set to > 0, it indicates
            # a preference for new tokens over existing ones. Verify that the
            # non-penalized token ID is not present in the output, while the
            # most penalized token is the one that occurs most frequently in
            # the output.
            assert non_penalized_token_id not in distinct_sorted_token_ids_in_output
            assert penalized_token_id == most_frequent_token_id
        elif frequency_penalty < 0:
            # If `frequency_penalty` is set to < 0, it indicates
            # a preference for existing tokens over new ones. Verify that the
            # non-penalized token ID is the one that occurs most frequently
            # in the output, while the penalized token ID is one that has not
            # yet appeared.
            assert non_penalized_token_id == most_frequent_token_id
            assert penalized_token_id not in distinct_sorted_token_ids_in_output