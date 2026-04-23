def test_selective_scan_varlen(
    with_padding,
    is_variable_B,
    is_variable_C,
    varBC_groups,
    has_D,
    has_z,
    has_delta_bias,
    delta_softplus,
    return_last_state,
    seqlen,
    itype,
    wtype,
):
    if varBC_groups > 1 and (not is_variable_B or not is_variable_C):
        pytest.skip()  # This config is not applicable
    device = "cuda"
    rtol, atol = (6e-4, 2e-3) if itype == torch.float32 else (3e-3, 5e-3)
    if itype == torch.bfloat16:
        rtol, atol = 3e-2, 5e-2
    rtolw, atolw = (1e-3, 1e-3)
    if has_z:  # If we have z, the errors on the weights seem higher
        rtolw = max(rtolw, rtol)
        atolw = max(atolw, atol)
    # set seed
    torch.random.manual_seed(0)
    seqlens = []
    batch_size = 4
    if seqlen < 10:
        batch_size = 1
    padding = 3 if with_padding else 0
    padded_batch_size = batch_size + padding

    if with_padding and seqlen < padded_batch_size:
        pytest.skip()

    nsplits = padded_batch_size - 1
    eos_pos = torch.randperm(seqlen - 1)[:nsplits].sort().values
    seqlens.append(
        torch.diff(
            torch.cat([torch.tensor([-1]), eos_pos, torch.tensor([seqlen - 1])])
        ).tolist()
    )

    assert sum(seqlens[-1]) == seqlen
    assert all(s > 0 for s in seqlens[-1])

    total_entries = batch_size * 10
    cumsum = torch.cumsum(torch.tensor(seqlens[0]), dim=0).to(torch.int32)
    cumsum = torch.concat([torch.tensor([0], dtype=torch.int32), cumsum], dim=0).cuda()

    dim = 4
    dstate = 8
    A = -0.5 * torch.rand(dim, dstate, device=device, dtype=wtype)
    A_ref = A.clone()
    B_shape = [varBC_groups, dstate, seqlen]
    B = torch.randn(B_shape, device=device, dtype=wtype if not is_variable_B else itype)
    B_ref = B.clone()
    C_shape = [varBC_groups, dstate, seqlen]
    C = torch.randn(C_shape, device=device, dtype=wtype if not is_variable_C else itype)
    C_ref = C.clone()
    D = torch.randn(dim, device=device, dtype=torch.float32) if has_D else None
    D_ref = D.clone() if D is not None else None
    z = torch.randn(dim, seqlen, device=device, dtype=itype)
    z_ref = z.clone()
    delta_bias = (
        (0.5 * torch.rand(dim, device=device, dtype=torch.float32))
        if has_delta_bias
        else None
    )
    u = torch.randn(dim, seqlen, device=device, dtype=itype)
    u_ref = u.clone()
    delta = 0.5 * torch.rand(dim, seqlen, device=device, dtype=itype)
    delta_ref = delta.clone()
    out = None
    out_ref = None

    prev_state_shape = (total_entries, u.shape[0], int(A.shape[1]))
    prev_state = torch.randn(
        prev_state_shape, device=u.device, dtype=itype, requires_grad=False
    )
    prev_state_ref = prev_state.clone()
    # +1 to exclude index 0 (null block)
    state_indices = (
        torch.randperm(total_entries - 1, dtype=torch.int32, device=u.device)[
            :batch_size
        ]
        + 1
    )
    unused_states_bool = torch.ones(total_entries, dtype=torch.bool, device=device)
    unused_states_bool[state_indices] = False
    padded_state_indices = torch.concat(
        [
            state_indices,
            torch.as_tensor(
                [NULL_BLOCK_ID] * padding, dtype=torch.int32, device=device
            ),
        ],
        dim=-1,
    )

    has_initial_state = torch.randint(
        0, 2, (cumsum.shape[0] - 1,), dtype=torch.bool, device=u.device
    )
    out = selective_scan_fn(
        u,
        prev_state,
        delta,
        A,
        B,
        C,
        D,
        z,
        delta_bias,
        delta_softplus,
        cumsum,
        padded_state_indices,
        has_initial_state,
    )
    outs_ref = []
    splits = [
        torch.split(var, seqlens[0], dim=-1)
        for var in (u_ref, delta_ref, B_ref, C_ref, z_ref)
    ]
    for i in range(len(seqlens[0])):
        u_s, delta_s, B_s, C_s, z_s = (v[i].unsqueeze(0) for v in splits)
        if padded_state_indices[i] == NULL_BLOCK_ID:
            continue
        out_ref_s, _ = selective_scan_ref(
            u_s,
            delta_s,
            A_ref,
            B_s,
            C_s,
            D_ref,
            z=z_s,
            delta_bias=delta_bias,
            delta_softplus=delta_softplus,
            return_last_state=return_last_state,
            prev_state=prev_state_ref[padded_state_indices[i]].unsqueeze(0)
            if has_initial_state[i]
            else None,
            final_state_out=prev_state_ref[padded_state_indices[i]].unsqueeze(0),
        )
        outs_ref.append(out_ref_s)
    out_ref = torch.cat(outs_ref, dim=-1)[0]

    unpadded_out = out[:, : out_ref[0].shape[-1]]
    print("Output diff max", (unpadded_out - out_ref).max())
    print("Output diff mean", (unpadded_out - out_ref).mean())
    print("Output state diff max", (prev_state - prev_state_ref).max())
    print("Output state diff mean", (prev_state - prev_state_ref).mean())
    assert torch.allclose(prev_state, prev_state_ref, rtol=rtol, atol=atol)
    assert torch.allclose(unpadded_out, out_ref, rtol=rtol, atol=atol)
    selective_scan_opcheck_fn(
        u,
        delta,
        A,
        B,
        C,
        D,
        z,
        delta_bias,
        delta_softplus,
        cumsum,
        padded_state_indices,
        has_initial_state,
        prev_state,
        block_size=2048,
    )