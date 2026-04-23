def generate_continuous_batched_examples(
    example_lens_by_batch,
    num_examples,
    full_length,
    last_taken,
    exhausted,
    n_heads,
    d_head,
    itype,
    device="cuda",
    return_naive_ref=True,
):
    # this function generates a random examples of certain length
    # and then cut according to "example_lens_by_batch" and feed
    # them in continuous batches to the kernels.
    # If if return_naive_ref=True, the naive torch implementation
    # ssd_minimal_discrete will be used to compute and return
    # reference output.

    # generate the full-length example
    A, dt, X, B, C = generate_random_inputs(
        num_examples, full_length, n_heads, d_head, itype
    )

    if return_naive_ref:
        Y_min, final_state_min = ssd_minimal_discrete(
            X * dt.unsqueeze(-1), A * dt, B, C, block_len=full_length // 4
        )

    # internal function that outputs a cont batch of examples
    # given a tuple of lengths for each example in the batch
    # e.g., example_lens=(8, 4) means take 8 samples from first eg,
    #       4 examples from second eg, etc
    def get_continuous_batch(example_lens: tuple[int, ...]):
        indices = []
        for i, x in enumerate(example_lens):
            c = last_taken.get(i, 0)
            indices.append((c, c + x))
            last_taken[i] = (c + x) % full_length
            exhausted[i] = last_taken[i] == 0

        return (
            torch.concat([x[i, s:e] for i, (s, e) in enumerate(indices)]).unsqueeze(0)
            for x in (dt, X, B, C)
        )

    # internal function that maps "n" to the appropriate right boundary
    # value when forming continuous batches from examples of length given
    # by "full_length".
    # - e.g., when n > full_length, returns n % full_length
    #         when n == full_length, returns full_length
    def end_boundary(n: int):
        return n - ((n - 1) // full_length) * full_length

    IND_E = None
    for spec in example_lens_by_batch:
        # get the (maybe partial) example seen in this cont batch
        dt2, X2, B2, C2 = get_continuous_batch(spec)

        # get the metadata
        cu_seqlens = torch.tensor((0,) + spec, device=device).cumsum(dim=0)
        seq_idx = torch.zeros(
            cu_seqlens[-1], dtype=torch.int32, device=cu_seqlens.device
        )
        for i, (srt, end) in enumerate(
            zip(
                cu_seqlens,
                cu_seqlens[1:],
            )
        ):
            seq_idx[srt:end] = i

        # for cont batch
        if IND_E is None:
            IND_S = [0 for _ in range(len(spec))]
        else:
            IND_S = [x % full_length for x in IND_E]
        IND_E = [end_boundary(x + y) for x, y in zip(IND_S, spec)]

        # varlen has implicit batch=1
        dt2 = dt2.squeeze(0)
        X2 = X2.squeeze(0)
        B2 = B2.squeeze(0)
        C2 = C2.squeeze(0)
        yield (
            [Y_min[s, IND_S[s] : IND_E[s]] for s in range(num_examples)]
            if return_naive_ref
            else None,
            cu_seqlens,
            seq_idx,
            (A, dt2, X2, B2, C2),
        )