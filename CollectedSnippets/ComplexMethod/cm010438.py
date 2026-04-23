def _check_for_seq_len_0_nested(params: SDPAParams, debug=False) -> bool:
    # When this function is called we are assured that the nt is dim==4
    q_is_safe = (
        _check_for_seq_len_0_and_consistent_head_dim_nested_helper(
            params.query, "query", debug
        )
        if params.query.is_nested
        else True
    )
    # short circuit if any is unsafe
    if not q_is_safe:
        return False

    k_is_safe = (
        _check_for_seq_len_0_and_consistent_head_dim_nested_helper(
            params.key, "key", debug
        )
        if params.key.is_nested
        else True
    )
    # short circuit if any is unsafe
    if not k_is_safe:
        return False

    v_is_safe = (
        _check_for_seq_len_0_and_consistent_head_dim_nested_helper(
            params.value, "value", debug
        )
        if params.value.is_nested
        else True
    )
    # short circuit if any is unsafe
    if not v_is_safe:
        return False

    # We now know none of the inputs have ragged num_heads, so we can safely
    # access .size(1)
    q_num_heads = params.query.size(1)
    k_num_heads = params.key.size(1)
    v_num_heads = params.value.size(1)
    same_num_heads = q_num_heads == k_num_heads and q_num_heads == v_num_heads

    if not same_num_heads:
        if (
            params.query.requires_grad
            or params.key.requires_grad
            or params.value.requires_grad
        ):
            if debug:
                log.warning(
                    "Both fused kernels do not support training with broadcasted NT inputs."
                )
            return False
        return _try_broadcast_param_size(
            q_num_heads, k_num_heads, v_num_heads, "num heads", debug
        )
    return True