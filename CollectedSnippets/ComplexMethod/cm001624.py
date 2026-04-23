def repair_config(sd_config, state_dict=None):
    if not hasattr(sd_config.model.params, "use_ema"):
        sd_config.model.params.use_ema = False

    if hasattr(sd_config.model.params, 'unet_config'):
        if shared.cmd_opts.no_half:
            sd_config.model.params.unet_config.params.use_fp16 = False
        elif shared.cmd_opts.upcast_sampling or shared.cmd_opts.precision == "half":
            sd_config.model.params.unet_config.params.use_fp16 = True

    if hasattr(sd_config.model.params, 'first_stage_config'):
        if getattr(sd_config.model.params.first_stage_config.params.ddconfig, "attn_type", None) == "vanilla-xformers" and not shared.xformers_available:
            sd_config.model.params.first_stage_config.params.ddconfig.attn_type = "vanilla"

    # For UnCLIP-L, override the hardcoded karlo directory
    if hasattr(sd_config.model.params, "noise_aug_config") and hasattr(sd_config.model.params.noise_aug_config.params, "clip_stats_path"):
        karlo_path = os.path.join(paths.models_path, 'karlo')
        sd_config.model.params.noise_aug_config.params.clip_stats_path = sd_config.model.params.noise_aug_config.params.clip_stats_path.replace("checkpoints/karlo_models", karlo_path)

    # Do not use checkpoint for inference.
    # This helps prevent extra performance overhead on checking parameters.
    # The perf overhead is about 100ms/it on 4090 for SDXL.
    if hasattr(sd_config.model.params, "network_config"):
        sd_config.model.params.network_config.params.use_checkpoint = False
    if hasattr(sd_config.model.params, "unet_config"):
        sd_config.model.params.unet_config.params.use_checkpoint = False