def get_moe_configs(
    E: int,
    N: int,
    dtype: str | None,
    block_n: int | None = None,
    block_k: int | None = None,
) -> dict[int, Any] | None:
    """
    Return optimized configurations for the fused MoE kernel.

    The return value will be a dictionary that maps an irregular grid of
    batch sizes to configurations of the fused_moe kernel. To evaluate the
    kernel on a given batch size bs, the closest batch size in the grid should
    be picked and the associated configuration chosen to invoke the kernel.
    """

    # Avoid optimizing for the batch invariant case. Use default config
    if envs.VLLM_BATCH_INVARIANT:
        return None

    # First look up if an optimized configuration is available in the configs
    # directory
    block_shape = [block_n, block_k] if block_n and block_k else None
    json_file_name = get_config_file_name(E, N, dtype, block_shape)

    config_file_paths = []

    # note that we prioritize user defined config
    user_defined_config_folder = envs.VLLM_TUNED_CONFIG_FOLDER
    if user_defined_config_folder is not None:
        user_defined_config_file_path = os.path.join(
            user_defined_config_folder, json_file_name
        )
        config_file_paths.append(user_defined_config_file_path)

    default_config_file_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "configs", json_file_name
    )
    config_file_paths.append(default_config_file_path)

    for config_file_path in config_file_paths:
        if os.path.exists(config_file_path):
            with open(config_file_path) as f:
                logger.info_once(
                    "Using configuration from %s for MoE layer.",
                    config_file_path,
                    scope="global",
                )
                # If a configuration has been found, return it
                tuned_config = json.load(f)
                # Delete triton_version from tuned_config
                tuned_config.pop("triton_version", None)
                return {int(key): val for key, val in tuned_config.items()}

    # If no optimized configuration is available, we will use the default
    # configuration
    logger.warning_once(
        "Using default MoE config. Performance might be sub-optimal! "
        "Config file not found at %s",
        ", ".join(config_file_paths),
    )
    return None