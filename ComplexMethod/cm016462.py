def free_memory(memory_required, device, keep_loaded=[], for_dynamic=False, pins_required=0, ram_required=0):
    cleanup_models_gc()
    unloaded_model = []
    can_unload = []
    unloaded_models = []

    for i in range(len(current_loaded_models) -1, -1, -1):
        shift_model = current_loaded_models[i]
        if device is None or shift_model.device == device:
            if shift_model not in keep_loaded and not shift_model.is_dead():
                can_unload.append((-shift_model.model_offloaded_memory(), sys.getrefcount(shift_model.model), shift_model.model_memory(), i))
                shift_model.currently_used = False

    can_unload_sorted = sorted(can_unload)
    for x in can_unload_sorted:
        i = x[-1]
        memory_to_free = 1e32
        pins_to_free = 1e32
        if not DISABLE_SMART_MEMORY or device is None:
            memory_to_free = 0 if device is None else memory_required - get_free_memory(device)
            pins_to_free = pins_required - get_free_ram()
            if current_loaded_models[i].model.is_dynamic() and for_dynamic:
                #don't actually unload dynamic models for the sake of other dynamic models
                #as that works on-demand.
                memory_required -= current_loaded_models[i].model.loaded_size()
                memory_to_free = 0
        if memory_to_free > 0 and current_loaded_models[i].model_unload(memory_to_free):
            logging.debug(f"Unloading {current_loaded_models[i].model.model.__class__.__name__}")
            unloaded_model.append(i)
        if pins_to_free > 0:
            logging.debug(f"PIN Unloading {current_loaded_models[i].model.model.__class__.__name__}")
            current_loaded_models[i].model.partially_unload_ram(pins_to_free)

    for x in can_unload_sorted:
        i = x[-1]
        ram_to_free = ram_required - psutil.virtual_memory().available
        if ram_to_free <= 0 and i not in unloaded_model:
            continue
        resident_memory, _ = current_loaded_models[i].model_mmap_residency(free=True)
        if resident_memory > 0:
            logging.debug(f"RAM Unloading {current_loaded_models[i].model.model.__class__.__name__}")

    for i in sorted(unloaded_model, reverse=True):
        unloaded_models.append(current_loaded_models.pop(i))

    if len(unloaded_model) > 0:
        soft_empty_cache()
    elif device is not None:
        if vram_state != VRAMState.HIGH_VRAM:
            mem_free_total, mem_free_torch = get_free_memory(device, torch_free_too=True)
            if mem_free_torch > mem_free_total * 0.25:
                soft_empty_cache()
    return unloaded_models