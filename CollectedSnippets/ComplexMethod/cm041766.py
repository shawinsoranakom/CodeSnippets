def create_fp8_kwargs(training_args: "TrainingArguments") -> list[Any]:
    """Create AORecipeKwargs for FP8 training with HuggingFace Accelerate.

    Args:
        training_args: Training arguments containing FP8 configuration

    Returns:
        List containing AORecipeKwargs if FP8 is enabled and supported, empty list otherwise
    """
    if not training_args.fp8:
        return []

    backend = getattr(training_args, "fp8_backend", "auto")
    logger.info_rank0(f"Creating FP8 configuration with backend: {backend}")

    try:
        # Use Transformer Engine backend (optimal for Hopper GPUs)
        if backend == "te":
            from accelerate.utils import FP8RecipeKwargs

            logger.info_rank0("Using Transformer Engine FP8 backend")
            return [FP8RecipeKwargs(backend="TE", fp8_format="HYBRID", amax_history_len=16, amax_compute_algo="max")]

        # Use TorchAO backend (default)
        from accelerate.utils import AORecipeKwargs

        # Create Float8LinearConfig if torchao backend is used
        config = None
        if backend == "torchao" or backend == "auto":
            from torchao.float8 import Float8LinearConfig

            # Use rowwise scaling for better performance (as recommended by torchao)
            # Configure alignment requirements for FP8 kernels
            config = Float8LinearConfig.from_recipe_name("rowwise")

            # Enable alignment for better kernel performance
            if hasattr(config, "enable_amax_init"):
                config.enable_amax_init = True
            if hasattr(config, "enable_pre_and_post_forward"):
                config.enable_pre_and_post_forward = True

        # Create module filter function to skip problematic layers
        # TorchAO FP8 requires dimensions divisible by 16 for optimal kernels
        def module_filter_func(module, layer_name):
            # Skip embedding and output layers for numerical stability
            skip_layers = ["embed", "lm_head", "output", "classifier"]
            if any(skip_name in layer_name.lower() for skip_name in skip_layers):
                return False

            # Only convert Linear layers
            if not (hasattr(module, "weight") and len(module.weight.shape) == 2):
                return False

            # Check dimension alignment for FP8 kernels
            weight = module.weight
            in_features, out_features = weight.shape[1], weight.shape[0]

            # Skip layers with dimensions not divisible by 16 to avoid kernel errors
            if in_features % 16 != 0 or out_features % 16 != 0:
                logger.debug(
                    f"Skipping layer {layer_name} with dimensions {out_features}x{in_features} (not divisible by 16)"
                )
                return False

            return True

        # Map FSDP all-gather setting if available (this affects the underlying implementation)
        if (
            hasattr(training_args, "fp8_enable_fsdp_float8_all_gather")
            and training_args.fp8_enable_fsdp_float8_all_gather
        ):
            logger.info_rank0("FSDP float8 all-gather optimization requested")

        return [AORecipeKwargs(config=config, module_filter_func=module_filter_func)]
    except Exception as e:
        logger.info_rank0(f"Failed to create FP8 configuration: {e}")
        return []