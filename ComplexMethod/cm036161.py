def native_sample_recovered_tokens(
    max_spec_len: int,
    num_draft_tokens: list[int],
    cu_num_draft_tokens: torch.Tensor,  # [batch_size]
    draft_token_ids: torch.Tensor,  # [num_tokens]
    draft_probs: torch.Tensor | None,  # [num_tokens, vocab_size]
    target_probs: torch.Tensor,  # [num_tokens, vocab_size]
    sampling_metadata: SamplingMetadata,
    device: torch.device,
) -> torch.Tensor:
    batch_size = len(num_draft_tokens)
    vocab_size = target_probs.shape[-1]

    q = torch.empty(
        (batch_size, vocab_size),
        dtype=torch.float32,
        device=device,
    )
    q.exponential_()

    states = {
        i: generator.get_state()
        for i, generator in sampling_metadata.generators.items()
    }
    for i, generator in sampling_metadata.generators.items():
        # Do not generate random numbers for requests with no draft tokens.
        # This can be important for reproducibility.
        if num_draft_tokens[i] > 0:
            q[i].exponential_(generator=generator)

        # In order to generate the same exponential later, reset the CUDA RNG
        # state because RNG state advances after each call.
        generator.set_state(states[i])

    inv_q = q.reciprocal()

    out = torch.empty_like(draft_token_ids)

    for req_idx in range(batch_size):
        start_idx = 0 if req_idx == 0 else int(cu_num_draft_tokens[req_idx - 1].item())
        end_idx = int(cu_num_draft_tokens[req_idx].item())
        num_tokens = end_idx - start_idx

        for pos in range(max_spec_len):
            if pos >= num_tokens:
                continue
            token_idx = start_idx + pos

            if draft_probs is None:
                # prob is target_probs[token_idx] except draft_token_id is zeroed
                prob = target_probs[token_idx].clone()
                draft_token_id = draft_token_ids[token_idx]
                prob[draft_token_id] = 0.0
            else:
                prob = (target_probs[token_idx] - draft_probs[token_idx]).clamp_min_(
                    0.0
                )

            score = prob * inv_q[req_idx]
            recovered_id = torch.argmax(score, dim=-1)
            out[token_idx] = recovered_id
    return out