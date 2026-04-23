def _init_infer_auto_device_map(
    model: nn.Module,
    max_memory: dict[int | str, int | str] | None = None,
    no_split_module_classes: set[str] | None = None,
    tied_parameters: list[list[str]] | None = None,
    hf_quantizer: "HfQuantizer | None" = None,
) -> tuple[
    list[int | str],
    dict[int | str, int | str],
    list[int | str],
    list[int],
    dict[str, int],
    list[list[str]],
    list[str],
    list[tuple[str, nn.Module]],
]:
    """
    Initialize variables required for computing the device map for model allocation.
    """
    max_memory = get_max_memory(max_memory)
    if no_split_module_classes is None:
        no_split_module_classes = []
    elif not isinstance(no_split_module_classes, (list, tuple, set)):
        no_split_module_classes = [no_split_module_classes]

    devices = list(max_memory.keys())
    if "disk" not in devices:
        devices.append("disk")
    gpus = [device for device in devices if device not in ["cpu", "disk"]]

    # Devices that need to keep space for a potential offloaded layer.
    if "mps" in gpus:
        main_devices = ["mps"]
    elif len(gpus) > 0:
        main_devices = [gpus[0], "cpu"]
    else:
        main_devices = ["cpu"]

    module_sizes, _ = compute_module_sizes(model, hf_quantizer, only_modules=False)

    if tied_parameters is None:
        if len(model.all_tied_weights_keys) > 0:
            # create a list of list of tied params based on unique tied groups
            groups = set(model.all_tied_weights_keys.values())
            tied_parameters = [
                sorted([k for k, v in model.all_tied_weights_keys.items() if v == target] + [target])
                for target in groups
            ]
        else:
            tied_parameters = [[]]

    # Direct submodules and parameters
    modules_to_treat = (
        list(model.named_parameters(recurse=False))
        + list(model.named_children())
        + list(model.named_buffers(recurse=False))
    )

    return (
        devices,
        max_memory,
        main_devices,
        gpus,
        module_sizes,
        tied_parameters,
        no_split_module_classes,
        modules_to_treat,
    )