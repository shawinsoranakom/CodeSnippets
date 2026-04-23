def load_vae(model, vae_file=None, vae_source="from unknown source"):
    global vae_dict, base_vae, loaded_vae_file
    # save_settings = False

    cache_enabled = shared.opts.sd_vae_checkpoint_cache > 0

    if vae_file:
        if cache_enabled and vae_file in checkpoints_loaded:
            # use vae checkpoint cache
            print(f"Loading VAE weights {vae_source}: cached {get_filename(vae_file)}")
            store_base_vae(model)
            _load_vae_dict(model, checkpoints_loaded[vae_file])
        else:
            assert os.path.isfile(vae_file), f"VAE {vae_source} doesn't exist: {vae_file}"
            print(f"Loading VAE weights {vae_source}: {vae_file}")
            store_base_vae(model)

            vae_dict_1 = load_vae_dict(vae_file, map_location=shared.weight_load_location)
            _load_vae_dict(model, vae_dict_1)

            if cache_enabled:
                # cache newly loaded vae
                checkpoints_loaded[vae_file] = vae_dict_1.copy()

        # clean up cache if limit is reached
        if cache_enabled:
            while len(checkpoints_loaded) > shared.opts.sd_vae_checkpoint_cache + 1: # we need to count the current model
                checkpoints_loaded.popitem(last=False)  # LRU

        # If vae used is not in dict, update it
        # It will be removed on refresh though
        vae_opt = get_filename(vae_file)
        if vae_opt not in vae_dict:
            vae_dict[vae_opt] = vae_file

    elif loaded_vae_file:
        restore_base_vae(model)

    loaded_vae_file = vae_file
    model.base_vae = base_vae
    model.loaded_vae_file = loaded_vae_file