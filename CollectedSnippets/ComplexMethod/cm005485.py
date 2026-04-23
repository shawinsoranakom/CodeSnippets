def accelerate_disk_offload(
    model: "PreTrainedModel",
    disk_offload_folder: str | None,
    checkpoint_files: list[str] | None,
    device_map: dict,
    sharded_metadata: dict | None,
    dtype: torch.dtype | None,
    weight_mapping=None,
):
    """
    Prepare the `disk_offload_index` that will be used for reading offloaded parameters. If reading from a safetensors
    file, parameters which do not need any special WeightConverter operation during loading (i.e. they are used as-is, or only
    renamed) will be mapped to where they already reside on disk. Otherwise, the parameters will be resaved inside
    `disk_offload_folder` during loading.
    """
    from ..core_model_loading import WeightRenaming, rename_source_key

    if disk_offload_folder is not None:
        os.makedirs(disk_offload_folder, exist_ok=True)
    is_offloaded_safetensors = checkpoint_files is not None and checkpoint_files[0].endswith(".safetensors")

    renamings = []
    if weight_mapping is not None:
        renamings = [entry for entry in weight_mapping if isinstance(entry, WeightRenaming)]

    # In this case, the offload index is simply the existing safetensors (except if using custom weight loading
    # Operation, e.g. the MoE models, where we need to resave the weights that were changed at loading time)
    if is_offloaded_safetensors:
        meta_state_dict = model.state_dict()
        param_device_map = expand_device_map(device_map, meta_state_dict.keys())
        str_dtype = str(dtype).replace("torch.", "") if dtype is not None else "float32"
        if sharded_metadata is None:
            weight_map = dict.fromkeys(safe_open(checkpoint_files[0], framework="pt").keys(), checkpoint_files[0])
        else:
            folder = os.path.sep.join(checkpoint_files[0].split(os.path.sep)[:-1])
            weight_map = {k: os.path.join(folder, v) for k, v in sharded_metadata["weight_map"].items()}

        # Update the weight names according to the `weight_mapping`
        weight_renaming_map = {
            rename_source_key(k, renamings, [], model.base_model_prefix, meta_state_dict)[0]: k for k in weight_map
        }

        # Prepare the index using existing safetensors files
        disk_offload_index = {
            target_name: {
                "safetensors_file": weight_map[source_name],
                "weight_name": source_name,
                "dtype": str_dtype,
            }
            for target_name, source_name in weight_renaming_map.items()
            # Need to check if it's in the mapping in case of unexpected keys that would result in KeyError (we skip them)
            if target_name in param_device_map and param_device_map[target_name] == "disk"
        }
    # In this case we will resave every offloaded weight
    else:
        disk_offload_index = {}

    return disk_offload_index