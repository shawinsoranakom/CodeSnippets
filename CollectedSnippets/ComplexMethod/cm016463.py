def load_models_gpu(models, memory_required=0, force_patch_weights=False, minimum_memory_required=None, force_full_load=False):
    cleanup_models_gc()
    global vram_state

    inference_memory = minimum_inference_memory()
    extra_mem = max(inference_memory, memory_required + extra_reserved_memory())
    if minimum_memory_required is None:
        minimum_memory_required = extra_mem
    else:
        minimum_memory_required = max(inference_memory, minimum_memory_required + extra_reserved_memory())

    models_temp = set()
    for m in models:
        models_temp.add(m)
        for mm in m.model_patches_models():
            models_temp.add(mm)

    models = models_temp

    models_to_load = []

    free_for_dynamic=True
    for x in models:
        if not x.is_dynamic():
            free_for_dynamic = False
        loaded_model = LoadedModel(x)
        try:
            loaded_model_index = current_loaded_models.index(loaded_model)
        except:
            loaded_model_index = None

        if loaded_model_index is not None:
            loaded = current_loaded_models[loaded_model_index]
            loaded.currently_used = True
            models_to_load.append(loaded)
        else:
            if hasattr(x, "model"):
                logging.info(f"Requested to load {x.model.__class__.__name__}")
            models_to_load.append(loaded_model)

    for loaded_model in models_to_load:
        to_unload = []
        for i in range(len(current_loaded_models)):
            if loaded_model.model.is_clone(current_loaded_models[i].model):
                to_unload = [i] + to_unload
        for i in to_unload:
            model_to_unload = current_loaded_models.pop(i)
            model_to_unload.model.detach(unpatch_all=False)
            model_to_unload.model_finalizer.detach()


    total_memory_required = {}
    total_pins_required = {}
    total_ram_required = {}
    for loaded_model in models_to_load:
        device = loaded_model.device
        total_memory_required[device] = total_memory_required.get(device, 0) + loaded_model.model_memory_required(device)
        resident_memory, model_memory = loaded_model.model_mmap_residency()
        pinned_memory = loaded_model.model.pinned_memory_size()
        #FIXME: This can over-free the pins as it budgets to pin the entire model. We should
        #make this JIT to keep as much pinned as possible.
        pins_required = model_memory - pinned_memory
        ram_required = model_memory - resident_memory
        total_pins_required[device] = total_pins_required.get(device, 0) + pins_required
        total_ram_required[device] = total_ram_required.get(device, 0) + ram_required

    for device in total_memory_required:
        if device != torch.device("cpu"):
            free_memory(total_memory_required[device] * 1.1 + extra_mem,
                        device,
                        for_dynamic=free_for_dynamic,
                        pins_required=total_pins_required[device],
                        ram_required=total_ram_required[device])

    for device in total_memory_required:
        if device != torch.device("cpu"):
            free_mem = get_free_memory(device)
            if free_mem < minimum_memory_required:
                models_l = free_memory(minimum_memory_required, device, for_dynamic=free_for_dynamic)
                logging.info("{} models unloaded.".format(len(models_l)))

    for loaded_model in models_to_load:
        model = loaded_model.model
        torch_dev = model.load_device
        if is_device_cpu(torch_dev):
            vram_set_state = VRAMState.DISABLED
        else:
            vram_set_state = vram_state
        lowvram_model_memory = 0
        if lowvram_available and (vram_set_state == VRAMState.LOW_VRAM or vram_set_state == VRAMState.NORMAL_VRAM) and not force_full_load:
            loaded_memory = loaded_model.model_loaded_memory()
            current_free_mem = get_free_memory(torch_dev) + loaded_memory

            lowvram_model_memory = max(0, (current_free_mem - minimum_memory_required), min(current_free_mem * MIN_WEIGHT_MEMORY_RATIO, current_free_mem - minimum_inference_memory()))
            lowvram_model_memory = lowvram_model_memory - loaded_memory

            if lowvram_model_memory == 0:
                lowvram_model_memory = 0.1

        if vram_set_state == VRAMState.NO_VRAM:
            lowvram_model_memory = 0.1

        loaded_model.model_load(lowvram_model_memory, force_patch_weights=force_patch_weights)
        current_loaded_models.insert(0, loaded_model)
    return