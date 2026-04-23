def process_images(p: StableDiffusionProcessing) -> Processed:
    if p.scripts is not None:
        p.scripts.before_process(p)

    stored_opts = {k: opts.data[k] if k in opts.data else opts.get_default(k) for k in p.override_settings.keys() if k in opts.data}

    try:
        # if no checkpoint override or the override checkpoint can't be found, remove override entry and load opts checkpoint
        # and if after running refiner, the refiner model is not unloaded - webui swaps back to main model here, if model over is present it will be reloaded afterwards
        if sd_models.checkpoint_aliases.get(p.override_settings.get('sd_model_checkpoint')) is None:
            p.override_settings.pop('sd_model_checkpoint', None)
            sd_models.reload_model_weights()

        for k, v in p.override_settings.items():
            opts.set(k, v, is_api=True, run_callbacks=False)

            if k == 'sd_model_checkpoint':
                sd_models.reload_model_weights()

            if k == 'sd_vae':
                sd_vae.reload_vae_weights()

        sd_models.apply_token_merging(p.sd_model, p.get_token_merging_ratio())

        # backwards compatibility, fix sampler and scheduler if invalid
        sd_samplers.fix_p_invalid_sampler_and_scheduler(p)

        with profiling.Profiler():
            res = process_images_inner(p)

    finally:
        sd_models.apply_token_merging(p.sd_model, 0)

        # restore opts to original state
        if p.override_settings_restore_afterwards:
            for k, v in stored_opts.items():
                setattr(opts, k, v)

                if k == 'sd_vae':
                    sd_vae.reload_vae_weights()

    return res