def get_or_autotune_moe_kernels(
    num_experts: int,
    hidden_dim: int,
    intermediate_dim: int,
    top_k: int,
    dtype: torch.dtype,
    force_autotune: bool = False,
    seq_len: int = 8192,
) -> Tuple[Any, Any, Any]:
    """
    Get cached kernel configurations or run auto-tuning.

    Args:
        num_experts: Number of experts in the MoE layer
        hidden_dim: Hidden dimension of the model
        intermediate_dim: Intermediate dimension for MoE MLP
        top_k: Number of experts to route to
        dtype: Data type for computation
        force_autotune: Force re-running autotuning even if cache exists
        seq_len: Sequence length to use for tuning benchmarks

    Returns:
        Tuple of (config_fwd, config_bwd_dx, config_bwd_dw)
    """
    device_capability = torch.cuda.get_device_capability()
    cache_key = _get_cache_key(
        num_experts,
        hidden_dim,
        intermediate_dim,
        top_k,
        dtype,
        device_capability,
        seq_len,
    )

    # 0. Check for environment variable override to DISABLE autotuning
    if os.environ.get("UNSLOTH_MOE_DISABLE_AUTOTUNE", "0") == "1":
        logger.info(
            f"UNSLOTH_MOE_DISABLE_AUTOTUNE=1: Using Heuristic (Safe) MoE kernel configs for SM{device_capability[0]}{device_capability[1]}"
        )
        return _get_heuristic_configs()
    if not force_autotune and cache_key in _kernel_config_cache:
        logger.info(f"Using in-memory cached MoE kernel configs: {cache_key}")
        return _kernel_config_cache[cache_key]

    # Try to load from disk
    if not force_autotune:
        cached_data = load_cached_config(cache_key)
        if cached_data is not None:
            # Reconstruct config objects from cached data
            try:
                from .grouped_gemm.kernels.tuning import (
                    KernelConfigForward,
                    KernelConfigBackward_dX,
                    KernelConfigBackward_dW,
                )

                config_fwd = KernelConfigForward(**cached_data["config_fwd"])
                config_bwd_dx = KernelConfigBackward_dX(**cached_data["config_bwd_dx"])
                config_bwd_dw = KernelConfigBackward_dW(**cached_data["config_bwd_dw"])

                configs = (config_fwd, config_bwd_dx, config_bwd_dw)
                _kernel_config_cache[cache_key] = configs
                return configs
            except Exception as e:
                logger.warning(f"Failed to reconstruct cached configs: {e}")

    # Run autotuning
    if cache_key in _autotune_completed and not force_autotune:
        logger.info(f"Autotuning already completed for: {cache_key}")
        return _kernel_config_cache[cache_key]

    logger.info(f"Running MoE kernel auto-tuning for: {cache_key}")
    logger.info(
        f"Configuration: {num_experts} experts, {hidden_dim} hidden, {intermediate_dim} intermediate, top_k={top_k}"
    )

    try:
        configs = _run_moe_autotuning(
            num_experts, hidden_dim, intermediate_dim, top_k, dtype, seq_len
        )

        # Cache the results
        _kernel_config_cache[cache_key] = configs
        _autotune_completed[cache_key] = True

        # Save to disk
        config_fwd, config_bwd_dx, config_bwd_dw = configs
        save_cached_config(
            cache_key,
            config_fwd,
            config_bwd_dx,
            config_bwd_dw,
            {
                "num_experts": num_experts,
                "hidden_dim": hidden_dim,
                "intermediate_dim": intermediate_dim,
            },
        )

        logger.info(f"MoE kernel auto-tuning completed: {cache_key}")
        return configs

    except Exception as e:
        logger.error(f"MoE kernel auto-tuning failed: {e}")
        if "AttributeError" in str(e) and "_experimental_make_tensor_descriptor" in str(
            e
        ):
            logger.warning(
                "Unsloth: Your Triton version might be incompatible with TMA features. Falling back to default configs."
            )
        logger.info("Falling back to default kernel configurations")
        return _get_default_configs()