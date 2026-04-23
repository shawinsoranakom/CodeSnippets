def flex_attention_forward(
    module: torch.nn.Module,
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attention_mask: Union[torch.Tensor, "BlockMask"],
    scaling: float | None = None,
    softcap: float | None = None,
    s_aux: torch.Tensor | None = None,
    **kwargs,
) -> tuple[torch.Tensor, torch.Tensor | None]:
    if kwargs.get("dropout", 0.0) > 0:
        raise ValueError(
            "`flex_attention` does not support `dropout`. Please use it with inference"
            " only (`model.eval()`) or turn off the attention dropout in the respective config."
        )

    block_mask = None
    score_mask = None
    if isinstance(attention_mask, BlockMask):
        block_mask = attention_mask
    else:
        score_mask = attention_mask

    if score_mask is not None:
        score_mask = score_mask[:, :, :, : key.shape[-2]]

    def score_mod(score, batch_idx, head_idx, q_idx, kv_idx):
        if softcap is not None:
            score = softcap * torch.tanh(score / softcap)
        if score_mask is not None:
            score = score + score_mask[batch_idx][0][q_idx][kv_idx]
        # Note: attention sinks cannot be correctly implemented in score_mod
        # because it requires operating on the full attention matrix before softmax.
        # ==> this is done after flex attention
        return score

    enable_gqa = True
    num_local_query_heads = query.shape[1]

    # When running TP this helps:
    if (num_local_query_heads & (num_local_query_heads - 1)) != 0:
        key = repeat_kv(key, query.shape[1] // key.shape[1])
        value = repeat_kv(value, query.shape[1] // value.shape[1])
        enable_gqa = False

    kernel_options = kwargs.get("kernel_options")
    # On CPU we must skip returning LSE due to a runtime issue; elsewhere, follow PyTorch API and return it
    return_lse = query.device.type != "cpu"

    if not return_lse and s_aux is not None:
        raise ValueError(
            "Attention sinks cannot be run on CPU with flex attention. Please switch to a different device, e.g. CUDA"
        )

    flex_attention_output = compile_friendly_flex_attention(
        query,
        key,
        value,
        score_mod=score_mod,
        block_mask=block_mask,
        enable_gqa=enable_gqa,
        scale=scaling,
        kernel_options=kernel_options,
        # Last time checked on PyTorch == 2.5.1: Flex Attention always computes the lse regardless.
        # For simplification, we thus always return it as no additional computations are introduced.
        training=module.training,
        # inject the lse args
        **get_flex_attention_lse_kwargs(return_lse),
    )

    if return_lse:
        # before torch 2.9, return_lse returns the LSE directly as a second tuple element
        # in torch 2.9 and later, return_aux returns AuxOutput as a second tuple element -- the LSE must be extracted
        if _TORCH_FLEX_USE_AUX:
            attention_output, aux = flex_attention_output  # type: ignore[misc]
            lse = aux.lse
        else:
            attention_output, lse = flex_attention_output  # type: ignore[misc]

        # lse is returned in float32
        lse = lse.to(value.dtype)

        if s_aux is not None:
            # Apply attention sinks by renormalizing using LSE
            batch_size, num_heads, seq_len_q, _ = attention_output.shape  # batch, num_heads, seq_len, head_dim
            sinks = s_aux.view(1, -1, 1, 1).expand(batch_size, num_heads, seq_len_q, 1)

            # We need to compute the normalization that includes the sinks
            # since log(sum(exp(scores))) = lse, exp(log(sum(exp(scores)))) = exp(lse)
            # NB: log(sum(exp(scores)) + exp(sink)) = log(exp(lse) + exp(sink))
            lse_expanded = lse.unsqueeze(-1)  # [batch, num_heads, seq_len, 1]
            combined_lse = torch.logsumexp(torch.cat([lse_expanded, sinks], dim=-1), dim=-1, keepdim=True)

            # Use new_norm / old_norm = exp(combined_lse - lse) to compute renorm and apply
            renorm_factor = torch.exp(lse_expanded - combined_lse)
            attention_output = attention_output * renorm_factor
            attention_output = attention_output.to(query.dtype)
    else:
        attention_output = flex_attention_output  # type: ignore[assignment]
        lse = None

    attention_output = attention_output.transpose(1, 2).contiguous()
    return attention_output, lse