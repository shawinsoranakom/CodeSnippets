def test_selective_state_update_with_num_accepted_tokens(
    dim, dstate, has_z, itype, max_seq_len
):
    device = "cuda"
    rtol, atol = (3e-4, 1e-3) if itype == torch.float32 else (5e-3, 1e-2)
    if itype == torch.bfloat16:
        rtol, atol = 5e-2, 1.5e-1
        if torch.version.hip:
            atol *= 2

    set_random_seed(0)
    batch_size = 4

    tokens_per_seq = torch.randint(1, max_seq_len + 1, (batch_size,), device=device)
    total_tokens = int(tokens_per_seq.sum().item())

    num_accepted_tokens = torch.randint(0, max_seq_len, (batch_size,), device=device)
    num_accepted_tokens[0] = 0  # Add edge-case of no accepted tokens
    num_accepted_tokens[1] = max_seq_len  # Add edge-case of all tokens accepted

    cu_seqlens = torch.tensor(
        [0] + torch.cumsum(tokens_per_seq, dim=0).tolist(),
        dtype=torch.int32,
        device=device,
    )

    total_state_slots = 50
    state = torch.randn(total_state_slots, dim, dstate, dtype=itype, device=device)

    state_batch_indices = torch.full(
        (batch_size, max_seq_len), NULL_BLOCK_ID, dtype=torch.int32, device=device
    )
    # Start from 1 to exclude null block at index 0
    initial_state_slots = torch.randint(
        1, 15, (batch_size,), device=device, dtype=torch.int32
    )
    for seq_idx in range(batch_size):
        token_pos = max(num_accepted_tokens[seq_idx].item() - 1, 0)
        state_batch_indices[seq_idx, token_pos] = initial_state_slots[seq_idx]

    dst_state_batch_indices = torch.full(
        (batch_size, max_seq_len), NULL_BLOCK_ID, dtype=torch.int32, device=device
    )
    slot_offset = 15
    dst_slots_map = {}
    for seq_idx in range(batch_size):
        for token_idx in range(tokens_per_seq[seq_idx].item()):
            dst_state_batch_indices[seq_idx, token_idx] = slot_offset
            dst_slots_map[(seq_idx, token_idx)] = slot_offset
            slot_offset += 1

    x = torch.randn(total_tokens, dim, device=device, dtype=itype)
    out = torch.empty_like(x)
    dt = torch.randn(total_tokens, dim, device=device, dtype=itype)
    dt_bias = torch.rand(dim, device=device) - 4.0
    A = -torch.rand(dim, dstate, device=device) - 1.0
    B = torch.randn(total_tokens, dstate, device=device)
    C = torch.randn(total_tokens, dstate, device=device)
    D = torch.randn(dim, device=device)
    z = torch.randn_like(x) if has_z else None

    state_ref_intermediate = {}
    out_ref_list = []

    for seq_idx in range(batch_size):
        seq_start = cu_seqlens[seq_idx].item()
        seq_end = cu_seqlens[seq_idx + 1].item()
        num_tokens = seq_end - seq_start

        token_pos = max(num_accepted_tokens[seq_idx].item() - 1, 0)
        initial_slot = state_batch_indices[seq_idx, token_pos].item()
        state_seq = state[initial_slot : initial_slot + 1].clone()

        for token_idx in range(num_tokens):
            global_idx = seq_start + token_idx

            out_token = selective_state_update_ref(
                state_seq,
                x[global_idx : global_idx + 1],
                dt[global_idx : global_idx + 1],
                A,
                B[global_idx : global_idx + 1],
                C[global_idx : global_idx + 1],
                D=D,
                z=z[global_idx : global_idx + 1] if z is not None else None,
                dt_bias=dt_bias,
                dt_softplus=True,
            )
            out_ref_list.append(out_token)
            state_ref_intermediate[(seq_idx, token_idx)] = state_seq.clone()

    out_ref = torch.cat(out_ref_list, dim=0)

    selective_state_update(
        state,
        x,
        dt,
        A,
        B,
        C,
        D=D,
        z=z,
        dt_bias=dt_bias,
        dt_softplus=True,
        out=out,
        cu_seqlens=cu_seqlens,
        state_batch_indices=state_batch_indices,
        dst_state_batch_indices=dst_state_batch_indices,
        num_accepted_tokens=num_accepted_tokens,
    )

    assert torch.allclose(out, out_ref, rtol=rtol, atol=atol)

    for seq_idx in range(batch_size):
        num_tokens = tokens_per_seq[seq_idx].item()
        for token_idx in range(num_tokens):
            dst_slot = dst_slots_map[(seq_idx, token_idx)]
            state_ref = state_ref_intermediate[(seq_idx, token_idx)].squeeze(0)
            assert torch.allclose(state[dst_slot], state_ref, rtol=rtol, atol=atol)