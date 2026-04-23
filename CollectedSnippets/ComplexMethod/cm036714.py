def test_selective_state_update_varlen(dim, dstate, has_z, itype, max_seq_len):
    device = "cuda"
    rtol, atol = (3e-4, 1e-3) if itype == torch.float32 else (5e-3, 1e-2)
    if itype == torch.bfloat16:
        rtol, atol = 5e-2, 1.5e-1
        if torch.version.hip:
            atol *= 2
    # set seed
    set_random_seed(0)
    batch_size = 4
    token_counts = torch.randint(1, max_seq_len + 1, (batch_size,), device=device)
    total_tokens = int(token_counts.sum().item())
    cu_seqlens = torch.tensor(
        [0] + torch.cumsum(token_counts, dim=0).tolist(),
        dtype=torch.int32,
        device=device,
    )
    state = torch.randn(batch_size, dim, dstate, dtype=itype, device=device)
    x = torch.randn(total_tokens, dim, device=device, dtype=itype)
    out = torch.empty_like(x)
    dt = torch.randn(total_tokens, dim, device=device, dtype=itype)
    dt_bias = torch.rand(dim, device=device) - 4.0
    A = -torch.rand(dim, dstate, device=device) - 1.0
    B = torch.randn(total_tokens, dstate, device=device)
    C = torch.randn(total_tokens, dstate, device=device)
    D = torch.randn(dim, device=device)
    z = torch.randn_like(x) if has_z else None
    state_ref = state.detach().clone()
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
    )

    out_ref_list = []
    for seq_idx in range(batch_size):
        start_idx = cu_seqlens[seq_idx].item()
        end_idx = cu_seqlens[seq_idx + 1].item()
        num_tokens = end_idx - start_idx
        for token_idx in range(num_tokens):
            idx = start_idx + token_idx
            out_ref_list.append(
                selective_state_update_ref(
                    state_ref[seq_idx : seq_idx + 1],
                    x[idx : idx + 1],
                    dt[idx : idx + 1],
                    A,
                    B[idx : idx + 1],
                    C[idx : idx + 1],
                    D=D,
                    z=z[idx : idx + 1] if z is not None else None,
                    dt_bias=dt_bias,
                    dt_softplus=True,
                )
            )
    out_ref = torch.cat(out_ref_list, dim=0)
    assert torch.allclose(state, state_ref, rtol=rtol, atol=atol)
    assert torch.allclose(out, out_ref, rtol=rtol, atol=atol)