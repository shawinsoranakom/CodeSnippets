def load_model_weights(model, checkpoint_info: CheckpointInfo, state_dict, timer):
    sd_model_hash = checkpoint_info.calculate_shorthash()
    timer.record("calculate hash")

    if devices.fp8:
        # prevent model to load state dict in fp8
        model.half()

    if not SkipWritingToConfig.skip:
        shared.opts.data["sd_model_checkpoint"] = checkpoint_info.title

    if state_dict is None:
        state_dict = get_checkpoint_state_dict(checkpoint_info, timer)

    set_model_type(model, state_dict)
    set_model_fields(model)

    if model.is_sdxl:
        sd_models_xl.extend_sdxl(model)

    if model.is_ssd:
        sd_hijack.model_hijack.convert_sdxl_to_ssd(model)

    if shared.opts.sd_checkpoint_cache > 0:
        # cache newly loaded model
        checkpoints_loaded[checkpoint_info] = state_dict.copy()

    if hasattr(model, "before_load_weights"):
        model.before_load_weights(state_dict)

    model.load_state_dict(state_dict, strict=False)
    timer.record("apply weights to model")

    if hasattr(model, "after_load_weights"):
        model.after_load_weights(state_dict)

    del state_dict

    # Set is_sdxl_inpaint flag.
    # Checks Unet structure to detect inpaint model. The inpaint model's
    # checkpoint state_dict does not contain the key
    # 'diffusion_model.input_blocks.0.0.weight'.
    diffusion_model_input = model.model.state_dict().get(
        'diffusion_model.input_blocks.0.0.weight'
    )
    model.is_sdxl_inpaint = (
        model.is_sdxl and
        diffusion_model_input is not None and
        diffusion_model_input.shape[1] == 9
    )

    if shared.cmd_opts.opt_channelslast:
        model.to(memory_format=torch.channels_last)
        timer.record("apply channels_last")

    if shared.cmd_opts.no_half:
        model.float()
        model.alphas_cumprod_original = model.alphas_cumprod
        devices.dtype_unet = torch.float32
        assert shared.cmd_opts.precision != "half", "Cannot use --precision half with --no-half"
        timer.record("apply float()")
    else:
        vae = model.first_stage_model
        depth_model = getattr(model, 'depth_model', None)

        # with --no-half-vae, remove VAE from model when doing half() to prevent its weights from being converted to float16
        if shared.cmd_opts.no_half_vae:
            model.first_stage_model = None
        # with --upcast-sampling, don't convert the depth model weights to float16
        if shared.cmd_opts.upcast_sampling and depth_model:
            model.depth_model = None

        alphas_cumprod = model.alphas_cumprod
        model.alphas_cumprod = None
        model.half()
        model.alphas_cumprod = alphas_cumprod
        model.alphas_cumprod_original = alphas_cumprod
        model.first_stage_model = vae
        if depth_model:
            model.depth_model = depth_model

        devices.dtype_unet = torch.float16
        timer.record("apply half()")

    apply_alpha_schedule_override(model)

    for module in model.modules():
        if hasattr(module, 'fp16_weight'):
            del module.fp16_weight
        if hasattr(module, 'fp16_bias'):
            del module.fp16_bias

    if check_fp8(model):
        devices.fp8 = True
        first_stage = model.first_stage_model
        model.first_stage_model = None
        for module in model.modules():
            if isinstance(module, (torch.nn.Conv2d, torch.nn.Linear)):
                if shared.opts.cache_fp16_weight:
                    module.fp16_weight = module.weight.data.clone().cpu().half()
                    if module.bias is not None:
                        module.fp16_bias = module.bias.data.clone().cpu().half()
                module.to(torch.float8_e4m3fn)
        model.first_stage_model = first_stage
        timer.record("apply fp8")
    else:
        devices.fp8 = False

    devices.unet_needs_upcast = shared.cmd_opts.upcast_sampling and devices.dtype == torch.float16 and devices.dtype_unet == torch.float16

    model.first_stage_model.to(devices.dtype_vae)
    timer.record("apply dtype to VAE")

    # clean up cache if limit is reached
    while len(checkpoints_loaded) > shared.opts.sd_checkpoint_cache:
        checkpoints_loaded.popitem(last=False)

    model.sd_model_hash = sd_model_hash
    model.sd_model_checkpoint = checkpoint_info.filename
    model.sd_checkpoint_info = checkpoint_info
    shared.opts.data["sd_checkpoint_hash"] = checkpoint_info.sha256

    if hasattr(model, 'logvar'):
        model.logvar = model.logvar.to(devices.device)  # fix for training

    sd_vae.delete_base_vae()
    sd_vae.clear_loaded_vae()
    vae_file, vae_source = sd_vae.resolve_vae(checkpoint_info.filename).tuple()
    sd_vae.load_vae(model, vae_file, vae_source)
    timer.record("load VAE")