def _build_reference_load_dict(
    original_state_dict: dict[str, torch.Tensor], reference_state_dict: dict[str, torch.Tensor]
) -> tuple[dict[str, torch.Tensor], list[str]]:
    loadable_reference_state_dict = {}
    skipped_reference_keys = []

    for key, value in original_state_dict.items():
        if not key.startswith("backbone."):
            continue

        stripped_key = key[len("backbone.") :]
        candidate_key = stripped_key

        if candidate_key.endswith(".ls1.gamma"):
            gamma_key = candidate_key.replace(".ls1.gamma", ".gamma_1")
            if gamma_key in reference_state_dict:
                candidate_key = gamma_key
        elif candidate_key.endswith(".ls2.gamma"):
            gamma_key = candidate_key.replace(".ls2.gamma", ".gamma_2")
            if gamma_key in reference_state_dict:
                candidate_key = gamma_key
        elif (
            candidate_key.endswith(".reg_token")
            and candidate_key.replace(".reg_token", ".register_tokens") in reference_state_dict
        ):
            candidate_key = candidate_key.replace(".reg_token", ".register_tokens")

        if candidate_key.endswith(".attn.qkv.bias"):
            base_key = candidate_key[: -len(".qkv.bias")]
            hidden_size = value.shape[0] // 3
            q_bias, _k_bias, v_bias = value.split(hidden_size, dim=0)
            q_bias_key = f"{base_key}.q_bias"
            v_bias_key = f"{base_key}.v_bias"
            if q_bias_key in reference_state_dict and v_bias_key in reference_state_dict:
                loadable_reference_state_dict[q_bias_key] = q_bias
                loadable_reference_state_dict[v_bias_key] = v_bias
                continue

        if candidate_key in reference_state_dict and tuple(reference_state_dict[candidate_key].shape) == tuple(
            value.shape
        ):
            loadable_reference_state_dict[candidate_key] = value
        else:
            skipped_reference_keys.append(stripped_key)

    return loadable_reference_state_dict, skipped_reference_keys