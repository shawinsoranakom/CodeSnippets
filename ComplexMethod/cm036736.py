def is_valid(
        a_type,
        b_type,
        c_type,
        group_blocks,
        m,
        n,
        k,
        e,
        topk,
        ep_size,
        act_order,
        is_k_full,
    ):
        group_size = group_blocks if group_blocks <= 0 else group_blocks * 16
        if group_size > 0 and k % group_size != 0:
            return False
        if act_order and group_size in [-1, k, n]:
            return False
        if group_size in [k, n]:
            return False
        if b_type == scalar_types.float8_e4m3fn and group_size == 32 and is_k_full:
            return False
        return a_type.size_bits < 16 or a_type is c_type