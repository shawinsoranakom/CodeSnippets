def load_model(checkpoint_info=None, already_loaded_state_dict=None):
    from modules import sd_hijack
    checkpoint_info = checkpoint_info or select_checkpoint()

    timer = Timer()

    if model_data.sd_model:
        send_model_to_trash(model_data.sd_model)
        model_data.sd_model = None
        devices.torch_gc()

    timer.record("unload existing model")

    if already_loaded_state_dict is not None:
        state_dict = already_loaded_state_dict
    else:
        state_dict = get_checkpoint_state_dict(checkpoint_info, timer)

    checkpoint_config = sd_models_config.find_checkpoint_config(state_dict, checkpoint_info)
    clip_is_included_into_sd = any(x for x in [sd1_clip_weight, sd2_clip_weight, sdxl_clip_weight, sdxl_refiner_clip_weight] if x in state_dict)

    timer.record("find config")

    sd_config = OmegaConf.load(checkpoint_config)
    repair_config(sd_config, state_dict)

    timer.record("load config")

    print(f"Creating model from config: {checkpoint_config}")

    sd_model = None
    try:
        with sd_disable_initialization.DisableInitialization(disable_clip=clip_is_included_into_sd or shared.cmd_opts.do_not_download_clip):
            with sd_disable_initialization.InitializeOnMeta():
                sd_model = instantiate_from_config(sd_config.model, state_dict)

    except Exception as e:
        errors.display(e, "creating model quickly", full_traceback=True)

    if sd_model is None:
        print('Failed to create model quickly; will retry using slow method.', file=sys.stderr)

        with sd_disable_initialization.InitializeOnMeta():
            sd_model = instantiate_from_config(sd_config.model, state_dict)

    sd_model.used_config = checkpoint_config

    timer.record("create model")

    if shared.cmd_opts.no_half:
        weight_dtype_conversion = None
    else:
        weight_dtype_conversion = {
            'first_stage_model': None,
            'alphas_cumprod': None,
            '': torch.float16,
        }

    with sd_disable_initialization.LoadStateDictOnMeta(state_dict, device=model_target_device(sd_model), weight_dtype_conversion=weight_dtype_conversion):
        load_model_weights(sd_model, checkpoint_info, state_dict, timer)

    timer.record("load weights from state dict")

    send_model_to_device(sd_model)
    timer.record("move model to device")

    sd_hijack.model_hijack.hijack(sd_model)

    timer.record("hijack")

    sd_model.eval()
    model_data.set_sd_model(sd_model)
    model_data.was_loaded_at_least_once = True

    sd_hijack.model_hijack.embedding_db.load_textual_inversion_embeddings(force_reload=True)  # Reload embeddings after model load as they may or may not fit the model

    timer.record("load textual inversion embeddings")

    script_callbacks.model_loaded_callback(sd_model)

    timer.record("scripts callbacks")

    with devices.autocast(), torch.no_grad():
        sd_model.cond_stage_model_empty_prompt = get_empty_cond(sd_model)

    timer.record("calculate empty prompt")

    print(f"Model loaded in {timer.summary()}.")

    return sd_model