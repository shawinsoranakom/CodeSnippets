def get_max_memory(max_memory: dict[int | str, int | str] | None = None):
    """
    Get the maximum memory available if nothing is passed, converts string to int otherwise.
    Note: we need to overwrite this as accelerate does not take into account torch allocated but unused device memory...
    """
    # Get the max memory (it only uses free gpu memory, not torch allocated but free memory...)
    final_max_memory = accelerate_max_memory(max_memory)

    # Adjust for allocated but free memory
    for device_name in final_max_memory:
        if isinstance(device_name, int):  # it's a GPU device
            # Only cuda and xpu use caching memory allocator
            if is_torch_xpu_available():
                unused_memory = torch.xpu.memory_reserved(device_name) - torch.xpu.memory_allocated(device_name)
            elif torch.cuda.is_available():
                unused_memory = torch.cuda.memory_reserved(device_name) - torch.cuda.memory_allocated(device_name)
            else:
                unused_memory = 0
            # Add the pre-allocated but unused device memory
            final_max_memory[device_name] += unused_memory
        # Still respect the `max_memory` passed by the user if any
        if max_memory is not None and device_name in max_memory:
            final_max_memory[device_name] = min(max_memory[device_name], final_max_memory[device_name])

    # If the user does not provide `max_memory`, accelerate sets the WHOLE cpu available memory as available.
    # This is unwanted, as we don't want to set extremely tight bound and pressure for cpu if we are memory-constrained,
    # especially if the model uses WeightConverter (because there will be some uncontrollable cpu memory spikes during
    # the conversions before we resave the weights). In those cases, it's better to offload to disk a bit more
    # if we were in-between, as otherwise we blow-up cpu memory
    if max_memory is None and "cpu" in final_max_memory:
        final_max_memory["cpu"] *= 0.90

    return final_max_memory