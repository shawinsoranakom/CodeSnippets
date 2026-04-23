def reload_model_weights(sd_model=None, info=None, forced_reload=False):
    checkpoint_info = info or select_checkpoint()

    timer = Timer()

    if not sd_model:
        sd_model = model_data.sd_model

    if sd_model is None:  # previous model load failed
        current_checkpoint_info = None
    else:
        current_checkpoint_info = sd_model.sd_checkpoint_info
        if check_fp8(sd_model) != devices.fp8:
            # load from state dict again to prevent extra numerical errors
            forced_reload = True
        elif sd_model.sd_model_checkpoint == checkpoint_info.filename and not forced_reload:
            return sd_model

    sd_model = reuse_model_from_already_loaded(sd_model, checkpoint_info, timer)
    if not forced_reload and sd_model is not None and sd_model.sd_checkpoint_info.filename == checkpoint_info.filename:
        return sd_model

    if sd_model is not None:
        sd_unet.apply_unet("None")
        send_model_to_cpu(sd_model)
        sd_hijack.model_hijack.undo_hijack(sd_model)

    state_dict = get_checkpoint_state_dict(checkpoint_info, timer)

    checkpoint_config = sd_models_config.find_checkpoint_config(state_dict, checkpoint_info)

    timer.record("find config")

    if sd_model is None or checkpoint_config != sd_model.used_config:
        if sd_model is not None:
            send_model_to_trash(sd_model)

        load_model(checkpoint_info, already_loaded_state_dict=state_dict)
        return model_data.sd_model

    try:
        load_model_weights(sd_model, checkpoint_info, state_dict, timer)
    except Exception:
        print("Failed to load checkpoint, restoring previous")
        load_model_weights(sd_model, current_checkpoint_info, None, timer)
        raise
    finally:
        sd_hijack.model_hijack.hijack(sd_model)
        timer.record("hijack")

        if not sd_model.lowvram:
            sd_model.to(devices.device)
            timer.record("move model to device")

        script_callbacks.model_loaded_callback(sd_model)
        timer.record("script callbacks")

    print(f"Weights loaded in {timer.summary()}.")

    model_data.set_sd_model(sd_model)
    sd_unet.apply_unet()

    return sd_model