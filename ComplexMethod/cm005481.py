def compute_module_sizes(
    model: "PreTrainedModel",
    hf_quantizer: "HfQuantizer | None" = None,
    buffers_only: bool = False,
    only_modules: bool = True,
) -> tuple[dict[str, int], dict[str, int]]:
    """
    Compute the size of each submodule of a given model (in bytes).
    Returns a tuple of 2 dicts, the fist one containing a mapping of all the modules and the corresponding size
    in bytes, and the 2nd one containing a mapping from all leaf modules (modules containing parameters, the end of
    the model graph) and the corresponding sizes.
    If `only_modules` is set to False, the first mapping will not only contain the size of all modules, but also
    the size of all parameters and buffers.
    """
    all_module_sizes = defaultdict(int)
    leaves_module_sizes = defaultdict(int)

    if buffers_only:
        iterator = model.named_buffers()
    else:
        # We need parameters + buffers here, as state_dict does not count non-persistent buffers which are taking space
        def all_tensors():
            yield from model.named_parameters()
            yield from model.named_buffers()

        iterator = all_tensors()

    tied_keys = getattr(model, "all_tied_weights_keys", {}).keys()
    for name, param in iterator:
        # Do not count tied keys (the model is usually not tied yet here, so they will appear in the iterator)
        # If the model is already tied, then they simply do not appear in the iterator anyway (remove_duplicates=True by default)
        if name in tied_keys:
            continue
        if hf_quantizer is not None:
            dtype_size = hf_quantizer.param_element_size(model, name, param)
        else:
            dtype_size = param.element_size()
        size = param.numel() * dtype_size
        name_parts = name.split(".")
        for idx in range(len(name_parts)):
            all_module_sizes[".".join(name_parts[:idx])] += size
        if "." in name:
            leaves_module_sizes[name.rsplit(".", 1)[0]] += size
        # If we want to also have the full leaves in `all_module_sizes`
        if not only_modules:
            all_module_sizes[name] += size

    return all_module_sizes, leaves_module_sizes