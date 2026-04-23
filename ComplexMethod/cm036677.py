def is_invalid(
        a_type,
        b_type,
        c_type,
        group_blocks,
        size_m,
        size_n,
        size_k,
        act_order,
        is_k_full,
        use_atomic_add,
        use_fp32_reduce,
    ):
        if use_atomic_add:
            if use_fp32_reduce:
                return False
            if (
                c_type == scalar_types.bfloat16
                and torch.cuda.get_device_capability()[0] < 9
            ):
                return False

        group_size = group_blocks if group_blocks <= 0 else group_blocks * 16
        if group_size > 0 and size_k % group_size != 0:
            return False

        if act_order and group_size in [-1, size_k]:
            return False
        if group_size == size_k:
            return False
        if not act_order and is_k_full:
            return False

        return a_type.size_bits < 16 or a_type is c_type