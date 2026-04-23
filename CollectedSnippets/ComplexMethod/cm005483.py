def get_balanced_memory(
    model: "PreTrainedModel",
    max_memory: dict[int | str, int | str] | None = None,
    no_split_module_classes: set[str] | None = None,
    hf_quantizer: "HfQuantizer | None" = None,
    low_zero: bool = False,
):
    """
    Compute a `max_memory` dictionary for [`infer_auto_device_map`] that will balance the use of each available GPU.

    <Tip>

    All computation is done analyzing sizes and dtypes of the model parameters. As a result, the model can be on the
    meta device (as it would if initialized within the `init_empty_weights` context manager).

    </Tip>

    Args:
        model (`PreTrainedModel`):
            The model to analyze.
        max_memory (`Dict`, *optional*):
            A dictionary device identifier to maximum memory. Will default to the maximum memory available if unset.
            Example: `max_memory={0: "1GB"}`.
        no_split_module_classes (`set[str]`, *optional*):
            A set of layer class names that should never be split across device (for instance any layer that has a
            residual connection).
        hf_quantizer (`HfQuantizer`, *optional*):
            A quantizer for the model.
        low_zero (`bool`, *optional*):
            Minimizes the number of weights on GPU 0, which is convenient when it's used for other operations (like the
            Transformers generate function).
    """
    # Get default / clean up max_memory
    user_not_set_max_memory = max_memory is None
    max_memory = get_max_memory(max_memory)
    # Check the number of accelerators available
    accelerator_max_memory = copy.deepcopy(max_memory)
    _, _ = accelerator_max_memory.pop("cpu", None), accelerator_max_memory.pop("disk", None)
    num_devices = len([d for d in accelerator_max_memory if accelerator_max_memory[d] > 0])

    if num_devices == 0:
        return max_memory

    if num_devices == 1:
        # We cannot do low_zero on just one GPU, but we will still reserve some memory for the buffer
        low_zero = False
        # If user just asked us to handle memory usage, we should avoid OOM
        if user_not_set_max_memory:
            for key in max_memory.keys():
                if isinstance(key, int):
                    max_memory[key] *= 0.9  # 90% is a good compromise
                    logger.info(
                        f"We will use 90% of the memory on device {key} for storing the model, and 10% for the buffer to avoid OOM. "
                        "You can set `max_memory` in to a higher value to use more memory (at your own risk)."
                    )
                    break  # only one device

    module_sizes, leave_modules_sizes = compute_module_sizes(model, hf_quantizer)
    per_gpu = module_sizes[""] // (num_devices - 1 if low_zero else num_devices)

    # We can't just set the memory to model_size // num_devices as it will end being too small: each GPU will get
    # slightly less layers and some layers will end up offload at the end. So this function computes a buffer size to
    # add which is the biggest of:
    # - the size of no split block (if applicable)
    # - the mean of the layer sizes
    if no_split_module_classes is None:
        no_split_module_classes = []
    elif not isinstance(no_split_module_classes, (list, tuple, set)):
        no_split_module_classes = [no_split_module_classes]

    # Identify the size of the no_split_block modules
    buffer = 0
    if len(no_split_module_classes) > 0:
        no_split_children = {}
        for name, size in module_sizes.items():
            if name == "":
                continue
            submodule = model.get_submodule(name)
            class_name = submodule.__class__.__name__
            if class_name in no_split_module_classes and class_name not in no_split_children:
                no_split_children[class_name] = size

            if set(no_split_children.keys()) == set(no_split_module_classes):
                break
        buffer = max(no_split_children.values()) if len(no_split_children) > 0 else 0

    mean_leaves = int(sum(leave_modules_sizes.values()) / max(len(leave_modules_sizes), 1))
    buffer = int(1.25 * max(buffer, mean_leaves))
    per_gpu += buffer

    # Sorted list of GPUs id (we may have some gpu ids not included in the our max_memory list - let's ignore them)
    gpus_idx_list = sorted(
        device_id for device_id, device_mem in max_memory.items() if isinstance(device_id, int) and device_mem > 0
    )
    # The last device is left with max_memory just in case the buffer is not enough.
    for idx in gpus_idx_list[:-1]:
        max_memory[idx] = min(max_memory[0] if low_zero and idx == 0 else per_gpu, max_memory[idx])

    if low_zero:
        min_zero = max(0, module_sizes[""] - sum([max_memory[i] for i in range(1, num_devices)]))
        max_memory[0] = min(min_zero, max_memory[0])

    return max_memory