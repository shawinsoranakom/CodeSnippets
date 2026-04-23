def caching_allocator_warmup(model: PreTrainedModel, expanded_device_map: dict, hf_quantizer: HfQuantizer | None):
    """This function warm-ups the caching allocator based on the size of the model tensors that will reside on each
    device. It allows to have one large call to Malloc, instead of recursively calling it later when loading
    the model, which is actually the loading speed bottleneck.
    Calling this function allows to cut the model loading time by a very large margin.

    A few facts related to loading speed (taking into account the use of this function):
    - When loading a model the first time, it is usually slower than the subsequent times, because the OS is very likely
    to cache the different state dicts (if enough resources/RAM are available)
    - Trying to force the OS to cache the files in advance (by e.g. accessing a small portion of them) is really hard,
    and not a good idea in general as this is low level OS optimizations that depend on resource usage anyway
    - As of 18/03/2025, loading a Llama 70B model with TP takes ~1 min without file cache, and ~13s with full file cache.
    The baseline, i.e. only loading the tensor shards on device and adjusting dtype (i.e. copying them) is ~5s with full cache.
    These numbers are reported for TP on 4 H100 GPUs.
    - It is useless to pre-allocate more than the model size in this function (i.e. using an `allocation_factor` > 1) as
    cudaMalloc is not a bottleneck at all anymore
    - Loading speed bottleneck is now almost only tensor copy (i.e. changing the dtype) and moving the tensors to the devices.
    However, we cannot really improve on those aspects obviously, as the data needs to be moved/copied in the end.
    """
    # Remove disk, cpu and meta devices, and cast to proper torch.device
    accelerator_device_map = {
        param: torch.device(device) for param, device in expanded_device_map.items() if is_accelerator_device(device)
    }
    if not accelerator_device_map:
        return

    total_byte_count = get_total_byte_count(model, accelerator_device_map, hf_quantizer)

    # This will kick off the caching allocator to avoid having to Malloc afterwards
    for device, byte_count in total_byte_count.items():
        if device.type in ["cuda", "xpu"]:
            accelerator_module = getattr(torch, device.type)
            index = device.index if device.index is not None else accelerator_module.current_device()
            free_device_memory, total_device_memory = accelerator_module.mem_get_info(index)
            unused_memory = accelerator_module.memory_reserved(index) - accelerator_module.memory_allocated(index)
            # If we have reserved but unused memory, we can lower the allocation we want to make, but only if it's still
            # higher than the unused memory. This is because otherwise torch will use that unused memory when performing
            # our own allocation, thus not allocating any new memory from the GPU. For example if byte_count=6 GiB,
            # unused_memory=4 GiB, then we cannot allocate only 2 GiB as this would *likely* (may not be exact, due to
            # fragmentation issues) simply use the pool of 4 GiB unused memory that is available. In those cases, it's better
            # to allocate more than the technically only 2 GiB required
            if byte_count - unused_memory > unused_memory:
                byte_count = byte_count - unused_memory
            # Minimum amount that will trigger new gpu allocation, even if it's technically "too much" compared to what we need
            elif byte_count - unused_memory > 1.5 * 1024**3:
                # Nothing we can do here, the memory will need to fill itself as we load params, but we cannot reallocate
                # from gpu until the unused memory is not filled
                if unused_memory + 1 > free_device_memory:
                    byte_count = 0
                # We allocate the minimum amount that will force new gpu allocation, even if it's technically "too much"
                else:
                    byte_count = unused_memory + 1
            # If we only need to reallocate less than 1.5 GiB of what is already allocated, then don't allocate more
            else:
                byte_count = 0
            # Allow up to (max device memory - 1.2 GiB) in resource-constrained hardware configurations. Trying to reserve more
            # than that amount might sometimes lead to unnecessary cuda/xpu OOM, if the last parameter to be loaded on the device is large,
            # and the remaining reserved memory portion is smaller than the param size -> torch will then try to fully re-allocate all
            # the param size, instead of using the remaining reserved part, and allocating only the difference, which can lead
            # to OOM. See https://github.com/huggingface/transformers/issues/37436#issuecomment-2808982161 for more details.
            # Note that we use an absolute value instead of device proportion here, as a 8GiB device could still allocate too much
            # if using e.g. 90% of device size, while a 140GiB device would allocate too little
            byte_count = min(byte_count, total_device_memory - 1.2 * 1024**3)
        # We divide by 2 here as we allocate in fp16
        _ = torch.empty(int(byte_count // 2), dtype=torch.float16, device=device, requires_grad=False)