def fp8_deepgemm_experts_forward(
    self: torch.nn.Module,
    hidden_states: torch.Tensor,
    top_k_index: torch.Tensor,
    top_k_weights: torch.Tensor,
) -> torch.Tensor:
    if self.activation_scheme == "static":
        raise NotImplementedError(
            "deepgemm experts dispatch does not support activation_scheme='static'. "
            "Use the default eager dispatch or switch to activation_scheme='dynamic'."
        )
    if self.block_size is None:
        raise ValueError(
            "DeepGEMM requires block-wise quantization (block_size=[128, 128]), "
            "but got per-tensor quantization (block_size=None)."
        )
    if self.block_size[0] != 128 or self.block_size[1] != 128:
        raise ValueError(f"DeepGEMM requires block_size=(128, 128), got {self.block_size}")

    _load_deepgemm_kernel()
    global deepgemm_grouped_fp8_matmul, deepgemm_per_token_cast_to_fp8

    device = hidden_states.device
    num_top_k = top_k_index.size(-1)
    num_tokens = hidden_states.size(0)
    hidden_dim = hidden_states.size(-1)

    # S is the number of selected token-expert pairs (S = num_tokens * num_top_k)
    token_idx = torch.arange(num_tokens, device=device).unsqueeze(1).expand(-1, num_top_k).reshape(-1)  # (S,)
    sample_weights = top_k_weights.reshape(-1)  # (S,)
    expert_ids = top_k_index.reshape(-1)  # (S,)

    # Sort by expert for grouped processing
    perm = torch.argsort(expert_ids)
    inv_perm = torch.empty_like(perm)
    inv_perm[perm] = torch.arange(perm.size(0), device=device)

    expert_ids_g = expert_ids[perm]
    sample_weights_g = sample_weights[perm]
    selected_hidden_states_g = hidden_states[token_idx[perm]]

    # Build TMA-aligned contiguous layout for DeepGEMM
    sorted_to_padded, grouped_layout, total_padded_rows = _build_deepgemm_contiguous_layout(
        expert_ids_g, self.num_experts, alignment=_DEEPGEMM_M_ALIGNMENT
    )

    # --- Up projection per expert (DeepGEMM grouped contiguous) ---
    w_up = self.gate_up_proj if self.has_gate else self.up_proj
    ws_up = self.gate_up_proj_scale_inv if self.has_gate else self.up_proj_scale_inv
    act_fp8, act_scales = deepgemm_per_token_cast_to_fp8(selected_hidden_states_g, use_ue8m0=False)
    act_fp8, act_scales = _pad_to_deepgemm_contiguous_layout(act_fp8, act_scales, sorted_to_padded, total_padded_rows)
    proj_out = torch.zeros(total_padded_rows, w_up.shape[1], device=device, dtype=torch.bfloat16)
    use_psum_layout = torch.cuda.get_device_capability(device)[0] >= 10
    deepgemm_grouped_fp8_matmul(
        (act_fp8, act_scales), (w_up, ws_up.float()), proj_out, grouped_layout, use_psum_layout=use_psum_layout
    )

    # Apply gating or activation
    if self.has_gate:
        proj_out = self._apply_gate(proj_out)
    else:
        proj_out = self.act_fn(proj_out)

    # --- Down projection per expert (DeepGEMM grouped contiguous) ---
    w_down = self.down_proj
    ws_down = self.down_proj_scale_inv
    proj_fp8, proj_scales = deepgemm_per_token_cast_to_fp8(proj_out, use_ue8m0=False)
    proj_out = torch.zeros(total_padded_rows, hidden_dim, device=device, dtype=torch.bfloat16)
    deepgemm_grouped_fp8_matmul(
        (proj_fp8, proj_scales), (w_down, ws_down.float()), proj_out, grouped_layout, use_psum_layout=use_psum_layout
    )

    # Remove padding rows
    proj_out = _unpad_from_deepgemm_contiguous_layout(proj_out, sorted_to_padded)

    # Apply routing weights
    weighted_out = proj_out * sample_weights_g.to(proj_out.dtype).unsqueeze(-1)  # (S, hidden_dim)

    # Restore original order
    weighted_out = weighted_out[inv_perm]

    # Accumulate results using deterministic reshape+sum instead of index_add_
    # (index_add_ with duplicate indices is non-deterministic on CUDA due to atomicAdd)
    final_hidden_states = weighted_out.view(num_tokens, num_top_k, hidden_dim).sum(dim=1)

    return final_hidden_states.to(hidden_states.dtype)