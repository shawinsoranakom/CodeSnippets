def test_deterministic_when_seeded(
    rejection_sampler,
    k: int,
    vocab_size: int,
    batch_size: int,
    frac_seeded: float,
    n_rep: int,
):
    num_tokens = batch_size * k
    draft_probs = torch.rand(
        num_tokens,
        vocab_size,
        dtype=torch.float32,
        device=DEVICE_TYPE,
    )
    draft_probs = F.softmax(draft_probs, dim=-1)
    target_logits = torch.rand_like(draft_probs)
    bonus_token_ids = torch.randint(
        low=0,
        high=vocab_size,
        size=(batch_size, 1),
        dtype=torch.int64,
        device=DEVICE_TYPE,
    )
    draft_token_ids = torch.randint(
        low=0,
        high=vocab_size,
        size=(batch_size, k),
        dtype=torch.int64,
        device=DEVICE_TYPE,
    )

    seeded_mask = torch.rand(batch_size, dtype=torch.float32) <= frac_seeded

    results = []
    for _ in range(n_rep):
        seeded_seqs = {
            i: torch.Generator(device=DEVICE_TYPE).manual_seed(i)
            for i in range(batch_size)
            if seeded_mask[i]
        }

        temperature = torch.ones(batch_size, dtype=torch.float32, device=DEVICE_TYPE)
        sampling_metadata = create_sampling_metadata(
            all_greedy=False, temperature=temperature, generators=seeded_seqs
        )
        spec_decode_metadata = create_spec_decode_metadata(
            draft_token_ids.tolist(), target_logits
        )

        mock_sampler_output(rejection_sampler, bonus_token_ids)
        rep_result = rejection_sampler(
            spec_decode_metadata,
            draft_probs=None,
            logits=target_logits,
            sampling_metadata=sampling_metadata,
        )

        results.append(rep_result.sampled_token_ids)

    for i in range(batch_size):
        if seeded_mask[i]:
            for j in range(1, n_rep):
                assert torch.equal(results[j][i], results[0][i])