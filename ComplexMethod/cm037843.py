def device_loading_context(module: torch.nn.Module, target_device: torch.device):
    if target_device.type == "cpu":
        # If target is CPU, no need to move anything
        yield module
        return

    original_device_states: dict[str, torch.device] = {}
    uva_offloaded_parameters: list[str] = []

    # Store original device states and move parameters to GPU if they're on CPU
    for name, p in module.named_parameters():
        if p.device.type == "cpu":
            original_device_states[name] = p.device
            p.data = p.data.to(target_device)
        if getattr(p, "_vllm_is_uva_offloaded", False):
            uva_offloaded_parameters.append(name)
        # Parameters already on target device are not touched

    try:
        yield module

    finally:
        use_pin_memory = (
            is_pin_memory_available()
            and not envs.VLLM_WEIGHT_OFFLOADING_DISABLE_PIN_MEMORY
        )
        # Restore parameters to their original devices, ignoring new parameters
        for name, p in module.named_parameters():
            if name in original_device_states:
                original_device: torch.device = original_device_states[name]
                p.data = p.data.to(original_device)

            # parameter is UVA offloaded, but was replaced with a new device tensor
            # re-offload it to CPU using UVA
            if name in uva_offloaded_parameters and not getattr(
                p, "_vllm_is_uva_offloaded", False
            ):
                cpu_data = p.data.to(device="cpu")
                if use_pin_memory:
                    cpu_data = cpu_data.pin_memory()
                p.data = get_accelerator_view_from_cpu_tensor(cpu_data)
                p._vllm_is_uva_offloaded = True