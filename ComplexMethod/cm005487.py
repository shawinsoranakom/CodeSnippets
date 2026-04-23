def infer_auto_device_map(
    model: nn.Module,
    max_memory: dict[int | str, int | str] | None = None,
    no_split_module_classes: set[str] | None = None,
    verbose: bool = False,
    clean_result: bool = True,
    offload_buffers: bool = False,
    tied_parameters: list[list[str]] | None = None,
    hf_quantizer: "HfQuantizer | None" = None,
):
    """
    Compute a device map for a given model giving priority to GPUs, then offload on CPU and finally offload to disk,
    such that:
    - we don't exceed the memory available of any of the GPU.
    - if offload to the CPU is needed, there is always room left on GPU 0 to put back the layer offloaded on CPU that
      has the largest size.
    - if offload to the CPU is needed,we don't exceed the RAM available on the CPU.
    - if offload to the disk is needed, there is always room left on the CPU to put back the layer offloaded on disk
      that has the largest size.

    <Tip>

    All computation is done analyzing sizes and dtypes of the model parameters. As a result, the model can be on the
    meta device (as it would if initialized within the `init_empty_weights` context manager).

    </Tip>

    Args:
        model (`torch.nn.Module`):
            The model to analyze.
        max_memory (`Dict`, *optional*):
            A dictionary device identifier to maximum memory. Will default to the maximum memory available if unset.
            Example: `max_memory={0: "1GB"}`.
        no_split_module_classes (`set[str]`, *optional*):
            A set of layer class names that should never be split across device (for instance any layer that has a
            residual connection).
        verbose (`bool`, *optional*, defaults to `False`):
            Whether or not to provide debugging statements as the function builds the device_map.
        clean_result (`bool`, *optional*, defaults to `True`):
            Clean the resulting device_map by grouping all submodules that go on the same device together.
        offload_buffers (`bool`, *optional*, defaults to `False`):
            In the layers that are offloaded on the CPU or the hard drive, whether or not to offload the buffers as
            well as the parameters.
    """

    # Initialize the variables
    (
        devices,
        max_memory,
        main_devices,
        gpus,
        module_sizes,
        tied_parameters,
        no_split_module_classes,
        modules_to_treat,
    ) = _init_infer_auto_device_map(model, max_memory, no_split_module_classes, tied_parameters, hf_quantizer)

    device_map = OrderedDict()
    current_device = 0
    device_memory_used = dict.fromkeys(devices, 0)
    device_buffer_sizes = {}
    device_minimum_assignment_memory = {}

    # Initialize maximum largest layer, to know which space to keep in memory
    max_layer_size, max_layer_names = get_max_layer_size(modules_to_treat, module_sizes, no_split_module_classes)

    # Ready ? This is going to be a bit messy.
    while len(modules_to_treat) > 0:
        name, module = modules_to_treat.pop(0)
        if verbose:
            print(f"\nTreating module {name}.")
        # Max size in the remaining layers may have changed since we took one, so we maybe update it.
        max_layer_names = [n for n in max_layer_names if n != name and not n.startswith(name + ".")]
        if len(max_layer_names) == 0:
            max_layer_size, max_layer_names = get_max_layer_size(
                [(n, m) for n, m in modules_to_treat if isinstance(m, torch.nn.Module)],
                module_sizes,
                no_split_module_classes,
            )
        # Assess size needed
        module_size = module_sizes[name]

        # We keep relevant tied parameters only: one of the tied parameters in the group is inside the current module
        # and the other is not.
        # Note: If we are currently processing the name `compute.weight`, an other parameter named
        # e.g. `compute.weight_submodule.parameter`
        # needs to be considered outside the current module, hence the check with additional dots.
        tied_param_groups = [
            tied_group
            for tied_group in tied_parameters
            if any(name + "." in k + "." for k in tied_group) and not all(name + "." in k + "." for k in tied_group)
        ]

        if verbose and len(tied_param_groups) > 0:
            print(f"  Found the relevant tied param groups {tied_param_groups}")

        # Then we keep track of all the parameters that are tied to the current module, but not in the current module
        tied_params = sum(
            [[p for p in tied_group if name + "." not in p + "."] for tied_group in tied_param_groups], []
        )

        if verbose and len(tied_params) > 0:
            print(f"  So those parameters need to be taken into account {tied_params}")

        device = devices[current_device]
        current_max_size = max_memory[device] if device != "disk" else None
        current_memory_reserved = 0
        # Reduce max size available by the largest layer.
        if devices[current_device] in main_devices:
            current_max_size = current_max_size - max_layer_size
            current_memory_reserved = max_layer_size

        module_size_with_ties, tied_module_names, tied_modules = get_module_size_with_ties(
            tied_params, module_size, module_sizes, modules_to_treat
        )

        # The module and its tied modules fit on the current device.
        if current_max_size is None or device_memory_used[device] + module_size_with_ties <= current_max_size:
            if verbose:
                output = f"Putting {name}"

                if tied_module_names:
                    output += f" and {tied_module_names}"
                else:
                    output += f" (size={module_size})"

                if current_max_size is not None:
                    output += f" (available={current_max_size - device_memory_used[device]})"

                output += f" on {device}."
                print(output)

            device_memory_used[device] += module_size_with_ties

            # Assign the primary module to the device.
            device_map[name] = device

            # Assign tied modules if any.
            for tied_module_name in tied_module_names:
                if tied_module_name in [m[0] for m in modules_to_treat]:
                    # Find the index of the tied module in the list
                    tied_module_index = next(i for i, (n, _) in enumerate(modules_to_treat) if n == tied_module_name)
                    # Remove the tied module from the list to prevent reprocessing
                    modules_to_treat.pop(tied_module_index)

                # Assign the tied module to the device
                device_map[tied_module_name] = device

            # Buffer Handling
            if not offload_buffers and isinstance(module, nn.Module):
                # Compute the total buffer size for the module
                current_buffer_size = compute_module_total_buffer_size(module, hf_quantizer)
                # Update the buffer size on the device
                device_buffer_sizes[device] = device_buffer_sizes.get(device, 0) + current_buffer_size

            continue

        # The current module itself fits, so we try to split the tied modules.
        if len(tied_params) > 0 and device_memory_used[device] + module_size <= current_max_size:
            # can we split one of the tied modules to make it smaller or do we need to go on the next device?
            if verbose:
                print(
                    f"Not enough space on {devices[current_device]} to put {name} and {tied_module_names} (space "
                    f"available {current_max_size - device_memory_used[device]}, needed size {module_size_with_ties})."
                )
            split_happened = False
            for tied_module_name, tied_module in zip(tied_module_names, tied_modules):
                tied_module_children = list(tied_module.named_children())
                if len(tied_module_children) == 0 or tied_module.__class__.__name__ in no_split_module_classes:
                    # can't break this one.
                    continue

                if verbose:
                    print(f"Splitting {tied_module_name}.")
                tied_module_children = list(tied_module.named_parameters(recurse=False)) + tied_module_children
                tied_module_children = [(f"{tied_module_name}.{n}", v) for n, v in tied_module_children]
                tied_module_index = [i for i, (n, _) in enumerate(modules_to_treat) if n == tied_module_name][0]

                modules_to_treat = (
                    [(name, module)]
                    + modules_to_treat[:tied_module_index]
                    + tied_module_children
                    + modules_to_treat[tied_module_index + 1 :]
                )
                # Update the max layer size.
                max_layer_size, max_layer_names = get_max_layer_size(
                    [(n, m) for n, m in modules_to_treat if isinstance(m, torch.nn.Module)],
                    module_sizes,
                    no_split_module_classes,
                )
                split_happened = True
                break

            if split_happened:
                continue

            # If the tied module is not split, we go to the next device
            if verbose:
                print("None of the tied module can be split, going to the next device.")

        # The current module itself doesn't fit, so we have to split it or go to the next device.
        if device_memory_used[device] + module_size >= current_max_size:
            # Split or not split?
            modules_children = (
                []
                if isinstance(module, nn.Parameter) or isinstance(module, torch.Tensor)
                else list(module.named_children())
            )
            if verbose:
                print(
                    f"Not enough space on {devices[current_device]} to put {name} (space available "
                    f"{current_max_size - device_memory_used[device]}, module size {module_size})."
                )
            if len(modules_children) == 0 or module.__class__.__name__ in no_split_module_classes:
                # -> no split, we go to the next device
                if verbose:
                    print("This module cannot be split, going to the next device.")

            else:
                # -> split, we replace the module studied by its children + parameters
                if verbose:
                    print(f"Splitting {name}.")
                modules_children = list(module.named_parameters(recurse=False)) + modules_children
                modules_to_treat = [(f"{name}.{n}", v) for n, v in modules_children] + modules_to_treat
                # Update the max layer size.
                max_layer_size, max_layer_names = get_max_layer_size(
                    [(n, m) for n, m in modules_to_treat if isinstance(m, torch.nn.Module)],
                    module_sizes,
                    no_split_module_classes,
                )
                continue

        if device_memory_used[device] == 0:
            device_minimum_assignment_memory[device] = module_size_with_ties + current_memory_reserved

        #  Neither the current module nor any tied modules can be split, so we move to the next device.
        device_memory_used[device] = device_memory_used[device] + current_memory_reserved
        current_device += 1
        modules_to_treat = [(name, module)] + modules_to_treat

    device_memory_used = {device: mem for device, mem in device_memory_used.items() if mem > 0}

    if clean_result:
        device_map = clean_device_map(device_map)

    non_gpu_buffer_size = device_buffer_sizes.get("cpu", 0) + device_buffer_sizes.get("disk", 0)
    if non_gpu_buffer_size > 0 and not offload_buffers:
        is_buffer_fit_any_gpu = False
        for gpu_device, gpu_max_memory in max_memory.items():
            if gpu_device == "cpu" or gpu_device == "disk":
                continue

            if not is_buffer_fit_any_gpu:
                gpu_memory_used = device_memory_used.get(gpu_device, 0)

                if gpu_max_memory >= non_gpu_buffer_size + gpu_memory_used:
                    is_buffer_fit_any_gpu = True

        if len(gpus) > 0 and not is_buffer_fit_any_gpu:
            logger.warning(
                f"Current model requires {non_gpu_buffer_size} bytes of buffer for offloaded layers, which seems does "
                f"not fit any GPU's remaining memory. If you are experiencing a OOM later, please consider using "
                f"offload_buffers=True."
            )

    if device_minimum_assignment_memory:
        devices_info = "\n".join(
            f"  - {device}: {mem} bytes required" for device, mem in device_minimum_assignment_memory.items()
        )
        logger.info(
            f"Based on the current allocation process, no modules could be assigned to the following devices due to "
            f"insufficient memory:\n"
            f"{devices_info}\n"
            f"These minimum requirements are specific to this allocation attempt and may vary. Consider increasing "
            f"the available memory for these devices to at least the specified minimum, or adjusting the model config."
        )

    check_tied_parameters_on_same_device(tied_parameters, device_map)
    return device_map