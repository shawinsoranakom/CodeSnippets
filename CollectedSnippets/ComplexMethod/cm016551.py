def load_bypass_lora_for_models(model, clip, lora, strength_model, strength_clip):
    """
    Load LoRA in bypass mode without modifying base model weights.

    Instead of patching weights, this injects the LoRA computation into the
    forward pass: output = base_forward(x) + lora_path(x)

    Non-adapter patches (bias diff, weight diff, etc.) are applied as regular patches.

    This is useful for training and when model weights are offloaded.
    """
    key_map = {}
    if model is not None:
        key_map = comfy.lora.model_lora_keys_unet(model.model, key_map)
    if clip is not None:
        key_map = comfy.lora.model_lora_keys_clip(clip.cond_stage_model, key_map)

    logging.debug(f"[BypassLoRA] key_map has {len(key_map)} entries")

    lora = comfy.lora_convert.convert_lora(lora)
    loaded = comfy.lora.load_lora(lora, key_map)

    logging.debug(f"[BypassLoRA] loaded has {len(loaded)} entries")

    # Separate adapters (for bypass) from other patches (for regular patching)
    bypass_patches = {}  # WeightAdapterBase instances -> bypass mode
    regular_patches = {}  # diff, set, bias patches -> regular weight patching

    for key, patch_data in loaded.items():
        if isinstance(patch_data, comfy.weight_adapter.WeightAdapterBase):
            bypass_patches[key] = patch_data
        else:
            regular_patches[key] = patch_data

    logging.debug(f"[BypassLoRA] {len(bypass_patches)} bypass adapters, {len(regular_patches)} regular patches")

    k = set()
    k1 = set()

    if model is not None:
        new_modelpatcher = model.clone()

        # Apply regular patches (bias diff, weight diff, etc.) via normal patching
        if regular_patches:
            patched_keys = new_modelpatcher.add_patches(regular_patches, strength_model)
            k.update(patched_keys)

        # Apply adapter patches via bypass injection
        manager = comfy.weight_adapter.BypassInjectionManager()
        model_sd_keys = set(new_modelpatcher.model.state_dict().keys())

        for key, adapter in bypass_patches.items():
            if key in model_sd_keys:
                manager.add_adapter(key, adapter, strength=strength_model)
                k.add(key)
            else:
                logging.warning(f"[BypassLoRA] Adapter key not in model state_dict: {key}")

        injections = manager.create_injections(new_modelpatcher.model)

        if manager.get_hook_count() > 0:
            new_modelpatcher.set_injections("bypass_lora", injections)
    else:
        new_modelpatcher = None

    if clip is not None:
        new_clip = clip.clone()

        # Apply regular patches to clip
        if regular_patches:
            patched_keys = new_clip.add_patches(regular_patches, strength_clip)
            k1.update(patched_keys)

        # Apply adapter patches via bypass injection
        clip_manager = comfy.weight_adapter.BypassInjectionManager()
        clip_sd_keys = set(new_clip.cond_stage_model.state_dict().keys())

        for key, adapter in bypass_patches.items():
            if key in clip_sd_keys:
                clip_manager.add_adapter(key, adapter, strength=strength_clip)
                k1.add(key)

        clip_injections = clip_manager.create_injections(new_clip.cond_stage_model)
        if clip_manager.get_hook_count() > 0:
            new_clip.patcher.set_injections("bypass_lora", clip_injections)
    else:
        new_clip = None

    for x in loaded:
        if (x not in k) and (x not in k1):
            patch_data = loaded[x]
            patch_type = type(patch_data).__name__
            if isinstance(patch_data, tuple):
                patch_type = f"tuple({patch_data[0]})"
            logging.warning(f"NOT LOADED: {x} (type={patch_type})")

    return (new_modelpatcher, new_clip)