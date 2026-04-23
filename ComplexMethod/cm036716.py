def test_selective_state_update_with_batch_indices(
    with_padding, dim, dstate, has_z, itype
):
    device = "cuda"
    rtol, atol = (3e-4, 1e-3) if itype == torch.float32 else (5e-3, 1e-2)
    if itype == torch.bfloat16:
        rtol, atol = 1e-1, 1e-1
        if torch.version.hip:
            atol *= 2
    # set seed
    torch.random.manual_seed(0)
    batch_size = 3
    padding = 5 if with_padding else 0
    padded_batch_size = batch_size + padding
    total_entries = 10 * batch_size
    state = torch.randn(total_entries, dim, dstate, dtype=itype, device=device)
    # +1 to exclude index 0 (null block)
    state_indices = (torch.randperm(total_entries - 1)[:batch_size] + 1).to(
        dtype=torch.int32, device=device
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
        dim=0,
    )
    x = torch.randn(padded_batch_size, dim, device=device, dtype=itype)
    out = torch.empty_like(x)
    dt = torch.randn(padded_batch_size, dim, device=device, dtype=itype)
    dt_bias = torch.rand(dim, device=device) - 4.0
    A = -torch.rand(dim, dstate, device=device) - 1.0
    B = torch.randn(padded_batch_size, dstate, device=device)
    C = torch.randn(padded_batch_size, dstate, device=device)
    D = torch.randn(dim, device=device)
    z = torch.randn_like(x) if has_z else None
    state_ref = state[state_indices, :].clone()
    state_before = state.clone()
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
        state_batch_indices=padded_state_indices,
        out=out,
    )
    out_ref = selective_state_update_ref(
        state_ref,
        x[:batch_size],
        dt[:batch_size],
        A,
        B[:batch_size],
        C[:batch_size],
        D=D,
        z=z[:batch_size] if z is not None else None,
        dt_bias=dt_bias,
        dt_softplus=True,
    )

    print("Output diff max", (out[:batch_size] - out_ref).max())
    print("Output diff mean", (out[:batch_size] - out_ref).mean())
    print("Output state diff max", (state[state_indices, :] - state_ref).max())
    print("Output state diff mean", (state[state_indices, :] - state_ref).mean())
    # test padded entries stay the same
    if with_padding:
        assert torch.equal(state_before[unused_states_bool], state[unused_states_bool])
        assert torch.equal(x[batch_size + 1 :], x[batch_size + 1 :])
        assert torch.equal(dt[batch_size + 1 :], dt[batch_size + 1 :])
        assert torch.equal(B[batch_size + 1 :], B[batch_size + 1 :])
        assert torch.equal(C[batch_size + 1 :], C[batch_size + 1 :])

    # test "real" entries
    assert torch.allclose(state[state_indices, :], state_ref, rtol=rtol, atol=atol)
    assert torch.allclose(out[:batch_size], out_ref, rtol=rtol, atol=atol)