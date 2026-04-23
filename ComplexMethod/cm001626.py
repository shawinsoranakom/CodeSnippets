def reuse_model_from_already_loaded(sd_model, checkpoint_info, timer):
    """
    Checks if the desired checkpoint from checkpoint_info is not already loaded in model_data.loaded_sd_models.
    If it is loaded, returns that (moving it to GPU if necessary, and moving the currently loadded model to CPU if necessary).
    If not, returns the model that can be used to load weights from checkpoint_info's file.
    If no such model exists, returns None.
    Additionally deletes loaded models that are over the limit set in settings (sd_checkpoints_limit).
    """

    if sd_model is not None and sd_model.sd_checkpoint_info.filename == checkpoint_info.filename:
        return sd_model

    if shared.opts.sd_checkpoints_keep_in_cpu:
        send_model_to_cpu(sd_model)
        timer.record("send model to cpu")

    already_loaded = None
    for i in reversed(range(len(model_data.loaded_sd_models))):
        loaded_model = model_data.loaded_sd_models[i]
        if loaded_model.sd_checkpoint_info.filename == checkpoint_info.filename:
            already_loaded = loaded_model
            continue

        if len(model_data.loaded_sd_models) > shared.opts.sd_checkpoints_limit > 0:
            print(f"Unloading model {len(model_data.loaded_sd_models)} over the limit of {shared.opts.sd_checkpoints_limit}: {loaded_model.sd_checkpoint_info.title}")
            del model_data.loaded_sd_models[i]
            send_model_to_trash(loaded_model)
            timer.record("send model to trash")

    if already_loaded is not None:
        send_model_to_device(already_loaded)
        timer.record("send model to device")

        model_data.set_sd_model(already_loaded, already_loaded=True)

        if not SkipWritingToConfig.skip:
            shared.opts.data["sd_model_checkpoint"] = already_loaded.sd_checkpoint_info.title
            shared.opts.data["sd_checkpoint_hash"] = already_loaded.sd_checkpoint_info.sha256

        print(f"Using already loaded model {already_loaded.sd_checkpoint_info.title}: done in {timer.summary()}")
        sd_vae.reload_vae_weights(already_loaded)
        return model_data.sd_model
    elif shared.opts.sd_checkpoints_limit > 1 and len(model_data.loaded_sd_models) < shared.opts.sd_checkpoints_limit:
        print(f"Loading model {checkpoint_info.title} ({len(model_data.loaded_sd_models) + 1} out of {shared.opts.sd_checkpoints_limit})")

        model_data.sd_model = None
        load_model(checkpoint_info)
        return model_data.sd_model
    elif len(model_data.loaded_sd_models) > 0:
        sd_model = model_data.loaded_sd_models.pop()
        model_data.sd_model = sd_model

        sd_vae.base_vae = getattr(sd_model, "base_vae", None)
        sd_vae.loaded_vae_file = getattr(sd_model, "loaded_vae_file", None)
        sd_vae.checkpoint_info = sd_model.sd_checkpoint_info

        print(f"Reusing loaded model {sd_model.sd_checkpoint_info.title} to load {checkpoint_info.title}")
        return sd_model
    else:
        return None