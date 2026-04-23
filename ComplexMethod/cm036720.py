def test_causal_conv1d_update_with_batch_gather(
    batch_size, with_padding, dim, width, seqlen, has_bias, silu_activation, itype
):
    device = "cuda"
    rtol, atol = (3e-4, 1e-3) if itype == torch.float32 else (3e-3, 5e-3)
    if itype == torch.bfloat16:
        rtol, atol = 1e-2, 5e-2

    # set seed
    set_random_seed(0)

    padding = 5 if with_padding else 0
    padded_batch_size = batch_size + padding
    # total_entries = number of cache line
    total_entries = 10 * batch_size

    # x will be (batch, dim, seqlen) with contiguous along dim-axis
    x = torch.randn(
        padded_batch_size, seqlen, dim, device=device, dtype=itype
    ).transpose(1, 2)

    x_ref = x.clone()

    # +1 to exclude index 0 (null block)
    conv_state_indices = (torch.randperm(total_entries - 1)[:batch_size] + 1).to(
        dtype=torch.int32, device=device
    )
    unused_states_bool = torch.ones(total_entries, dtype=torch.bool, device=device)
    unused_states_bool[conv_state_indices] = False
    padded_state_indices = torch.concat(
        [
            conv_state_indices,
            torch.as_tensor(
                [NULL_BLOCK_ID] * padding, dtype=torch.int32, device=device
            ),
        ],
        dim=0,
    )

    # conv_state will be (cache_lines, dim, state_len)
    # with contiguous along dim-axis
    conv_state = torch.randn(
        total_entries, width - 1, dim, device=device, dtype=itype
    ).transpose(1, 2)

    conv_state_for_padding_test = conv_state.clone()

    weight = torch.randn(dim, width, device=device, dtype=itype)
    bias = torch.randn(dim, device=device, dtype=itype) if has_bias else None
    conv_state_ref = conv_state[conv_state_indices, :].detach().clone()
    activation = None if not silu_activation else "silu"

    out = causal_conv1d_update(
        x,
        conv_state,
        weight,
        bias,
        activation=activation,
        conv_state_indices=padded_state_indices,
    )
    out_ref = causal_conv1d_update_ref(
        x_ref[:batch_size], conv_state_ref, weight, bias, activation=activation
    )

    assert torch.equal(conv_state[conv_state_indices, :], conv_state_ref)
    assert torch.equal(
        conv_state[unused_states_bool], conv_state_for_padding_test[unused_states_bool]
    )
    assert torch.allclose(out[:batch_size], out_ref, rtol=rtol, atol=atol)