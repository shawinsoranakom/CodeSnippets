def get_lora_op_configs(
    op_type: str,
    max_loras: int,
    batch: int,
    hidden_size: int,
    rank: int,
    num_slices: int,
    add_inputs: bool | None = None,
    moe_intermediate_size: int | None = None,
) -> dict[str, int | None]:
    # Add support for fused_moe_lora ops
    assert op_type in [
        "shrink",
        "expand",
        "fused_moe_lora_w13_shrink",
        "fused_moe_lora_w13_expand",
        "fused_moe_lora_w2_shrink",
        "fused_moe_lora_w2_expand",
    ]

    # default config
    default = {}
    if op_type == "shrink":
        split_k = 64 if batch < 128 else 8
        if is_batch_invariant:
            split_k = 1
        default = {
            "block_m": 32,
            "block_n": 16,
            "block_k": 256 if batch < 128 else 32,
            "split_k": split_k,
            "num_warps": 4,
            "num_ctas": 1,
            "group_size_m": 8,
            "num_stages": 2,
            "max_nreg": None,
        }
    # The default config for fused_moe_lora ops
    elif op_type in [
        "fused_moe_lora_w13_shrink",
        "fused_moe_lora_w2_shrink",
    ]:
        default = {
            "block_m": 64,
            "block_n": min(64, next_power_of_2(rank)),
            "block_k": 32,
            "num_warps": 4,
            "num_stages": 3,
            "group_size_m": 8,
            "split_k": 1,
        }
    elif op_type in [
        "fused_moe_lora_w13_expand",
        "fused_moe_lora_w2_expand",
    ]:
        default = {
            "block_m": 64,
            "block_n": 64,
            "block_k": max(16, min(32, next_power_of_2(rank))),
            "num_warps": 4,
            "num_stages": 3,
            "group_size_m": 8,
            "split_k": 1,
        }
    else:
        default = {
            "block_m": 64,
            "block_n": 64 if num_slices > 1 else 128,
            "block_k": 32,
            "num_warps": 4,
            "num_ctas": 1,
            "num_stages": 2,
            "max_nreg": None,
        }
    m = batch

    k, n = (hidden_size, rank) if op_type == "shrink" else (rank, hidden_size)

    config_data: Any
    config_data = load_lora_op_config(op_type, add_inputs)
    if not config_data:
        logger.warning_once("Using default LoRA kernel configs")
        return default

    # config is structured as config_data[max_loras][num_slices][m][k][n] = {}
    # slice by max_loras
    config_data = (
        config_data.get(str(max_loras))
        or config_data[min(config_data.keys(), key=lambda x: abs(int(x) - max_loras))]
    )
    # slice by num_slices
    config_data = config_data[str(num_slices)]
    # slice by m
    config_data = (
        config_data.get(str(m))
        or config_data[min(config_data.keys(), key=lambda x: abs(int(x) - m))]
    )
    # slice by k
    config_data = (
        config_data.get(str(k))
        or config_data[min(config_data.keys(), key=lambda x: abs(int(x) - k))]
    )
    # slice by n
    config_data = (
        config_data.get(str(n))
        or config_data[min(config_data.keys(), key=lambda x: abs(int(x) - n))]
    )

    # slice by moe-intermediate-size if applicable
    if moe_intermediate_size is not None:
        i = moe_intermediate_size
        config_data = (
            config_data.get(str(i))
            or config_data[min(config_data.keys(), key=lambda x: abs(int(x) - i))]
        )

    assert config_data is not None
    return config_data