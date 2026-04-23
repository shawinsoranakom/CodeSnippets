def load_hook_lora_for_models(model: ModelPatcher, clip: CLIP, lora: dict[str, torch.Tensor],
                              strength_model: float, strength_clip: float):
    key_map = {}
    if model is not None:
        key_map = comfy.lora.model_lora_keys_unet(model.model, key_map)
    if clip is not None:
        key_map = comfy.lora.model_lora_keys_clip(clip.cond_stage_model, key_map)

    hook_group = HookGroup()
    hook = WeightHook()
    hook_group.add(hook)
    loaded: dict[str] = comfy.lora.load_lora(lora, key_map)
    if model is not None:
        new_modelpatcher = model.clone()
        k = new_modelpatcher.add_hook_patches(hook=hook, patches=loaded, strength_patch=strength_model)
    else:
        k = ()
        new_modelpatcher = None

    if clip is not None:
        new_clip = clip.clone()
        k1 = new_clip.patcher.add_hook_patches(hook=hook, patches=loaded, strength_patch=strength_clip)
    else:
        k1 = ()
        new_clip = None
    k = set(k)
    k1 = set(k1)
    for x in loaded:
        if (x not in k) and (x not in k1):
            logging.warning(f"NOT LOADED {x}")
    return (new_modelpatcher, new_clip, hook_group)