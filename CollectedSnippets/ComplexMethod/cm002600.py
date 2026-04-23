def _load_pretrained_model(
        model: "PreTrainedModel",
        state_dict: dict | None,
        checkpoint_files: list[str] | None,
        load_config: LoadStateDictConfig,
        expected_keys: list[str] | None = None,
    ) -> tuple[LoadStateDictInfo, dict]:
        """Perform the actual loading of some checkpoints into a `model`, by reading them from disk and dispatching them accordingly."""
        is_quantized = load_config.is_quantized
        is_hqq_or_quark = is_quantized and load_config.hf_quantizer.quantization_config.quant_method in {
            QuantizationMethod.HQQ,
            QuantizationMethod.QUARK,
        }

        # Model's definition arriving here is final (TP hooks added, quantized layers replaces)
        expected_keys = list(model.state_dict().keys()) if expected_keys is None else expected_keys

        if logger.level >= logging.WARNING:
            verify_tp_plan(expected_keys, getattr(model, "_tp_plan", None))

        # This offload index if for params explicitly on the "disk" in the device_map
        disk_offload_index = None
        # Prepare parameters offloading if needed
        if load_config.device_map is not None and "disk" in load_config.device_map.values():
            disk_offload_index = accelerate_disk_offload(
                model,
                load_config.disk_offload_folder,
                checkpoint_files,
                load_config.device_map,
                load_config.sharded_metadata,
                load_config.dtype,
                load_config.weight_mapping,
            )

        # Warmup cuda to load the weights much faster on devices
        if load_config.device_map is not None and not is_hqq_or_quark:
            expanded_device_map = expand_device_map(load_config.device_map, expected_keys)
            caching_allocator_warmup(model, expanded_device_map, load_config.hf_quantizer)

        error_msgs = []

        if is_deepspeed_zero3_enabled() and not is_quantized:
            if state_dict is None:
                merged_state_dict = {}
                for ckpt_file in checkpoint_files:
                    merged_state_dict.update(
                        load_state_dict(
                            ckpt_file,
                            map_location="cpu",
                            weights_only=load_config.weights_only,
                            disable_mmap=load_config.disable_mmap,
                        )
                    )
                state_dict = merged_state_dict
            error_msgs, missing_keys = _load_state_dict_into_zero3_model(model, state_dict, load_config)
            # This is not true but for now we assume only best-case scenario with deepspeed, i.e. perfectly matching checkpoints
            loading_info = LoadStateDictInfo(
                missing_keys=missing_keys,
                error_msgs=error_msgs,
                unexpected_keys=set(),
                mismatched_keys=set(),
                conversion_errors={},
            )
        else:
            all_pointer = set()
            if state_dict is not None:
                merged_state_dict = state_dict
            elif checkpoint_files is not None and checkpoint_files[0].endswith(".safetensors") and state_dict is None:
                merged_state_dict = {}
                for file in checkpoint_files:
                    if load_config.disable_mmap or _is_on_hf_mount(file):
                        with open(file, "rb") as _fh:
                            merged_state_dict.update(_safe_load_bytes(_fh.read()))
                        continue
                    file_pointer = safe_open(file, framework="pt", device="cpu")
                    all_pointer.add(file_pointer)
                    for k in file_pointer.keys():
                        merged_state_dict[k] = file_pointer.get_slice(k)  # don't materialize yet
            # Checkpoints are .bin
            elif checkpoint_files is not None:
                merged_state_dict = {}
                for ckpt_file in checkpoint_files:
                    merged_state_dict.update(load_state_dict(ckpt_file, disable_mmap=load_config.disable_mmap))
            else:
                raise ValueError("Neither a state dict nor checkpoint files were found.")

            loading_info, disk_offload_index = convert_and_load_state_dict_in_model(
                model=model,
                state_dict=merged_state_dict,
                load_config=load_config,
                tp_plan=model.tp_plan,
                disk_offload_index=disk_offload_index,
            )

            # finally close all opened file pointers
            for k in all_pointer:
                k.__exit__(None, None, None)

        return loading_info, disk_offload_index