def test_causal_conv1d_varlen(
    batch, with_padding, dim, seqlen, width, has_bias, silu_activation, itype
):
    device = "cuda"
    torch.accelerator.empty_cache()
    rtol, atol = (3e-4, 1e-3) if itype == torch.float32 else (3e-3, 5e-3)
    if itype == torch.bfloat16:
        rtol, atol = 1e-2, 5e-2
    # set seed
    set_random_seed(0)
    seqlens = []
    batch_size = batch
    padding = 3 if with_padding else 0
    padded_batch_size = batch_size + padding
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
    cumsum = torch.concat([torch.tensor([0], dtype=torch.int32), cumsum], dim=0)
    x = rearrange(
        torch.randn(1, seqlen, 4096 + dim + 64, device=device, dtype=itype),
        "b s d -> b d s",
    )[:, 4096 : 4096 + dim, :]

    weight = torch.randn(dim, width, device=device, dtype=itype)

    bias = torch.randn(dim, device=device, dtype=itype) if has_bias else None
    x_ref = x.clone()
    weight_ref = weight.clone()
    bias_ref = bias.clone() if bias is not None else None
    activation = None if not silu_activation else "silu"
    final_states = torch.randn(
        total_entries, width - 1, dim, device=x.device, dtype=x.dtype
    ).transpose(1, 2)
    final_states_ref = final_states.clone()
    has_initial_states = torch.randint(
        0, 2, (cumsum.shape[0] - 1,), dtype=torch.bool, device=x.device
    )
    # +1 to exclude index 0 (null block)
    state_indices = (
        torch.randperm(total_entries - 1, dtype=torch.int32, device=x.device)[
            :batch_size
        ]
        + 1
    )
    padded_state_indices = torch.concat(
        [
            state_indices,
            torch.as_tensor(
                [NULL_BLOCK_ID] * padding, dtype=torch.int32, device=device
            ),
        ],
        dim=-1,
    )
    out = causal_conv1d_fn(
        x.squeeze(0),
        weight,
        bias=bias,
        conv_states=final_states,
        query_start_loc=cumsum.cuda(),
        cache_indices=padded_state_indices,
        has_initial_state=has_initial_states,
        activation=activation,
    )

    out_ref = []
    out_ref_b = []

    splits = [torch.split(var, seqlens[0], dim=-1) for var in (x_ref)]
    for i in range(len(seqlens[0])):
        x_s = [v[i].unsqueeze(0) for v in splits][0]
        if padded_state_indices[i] == NULL_BLOCK_ID:
            continue
        out_ref_b.append(
            causal_conv1d_ref(
                x_s,
                weight_ref,
                bias_ref,
                activation=activation,
                return_final_states=True,
                final_states_out=final_states_ref[padded_state_indices[i]].unsqueeze(0),
                initial_states=final_states_ref[padded_state_indices[i]].unsqueeze(0)
                if has_initial_states[i]
                else None,
            )
        )
    out_ref.append(torch.cat([t[0] for t in out_ref_b], dim=2))
    out_ref_tensor = torch.cat(out_ref, dim=0)

    assert torch.allclose(
        final_states[state_indices],
        final_states_ref[state_indices],
        rtol=rtol,
        atol=atol,
    )
    unpadded_out = out[:, : out_ref_tensor.shape[-1]]
    assert torch.allclose(unpadded_out, out_ref_tensor, rtol=rtol, atol=atol)