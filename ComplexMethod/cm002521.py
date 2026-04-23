def convert_and_load_state_dict_in_model(
    model: PreTrainedModel,
    state_dict: dict[str, Any],
    load_config: LoadStateDictConfig,
    tp_plan: dict[str, str] | None,
    disk_offload_index: dict | None = None,
):
    r"""
    We build a mapping from the keys obtained by renaming each of the checkpoint keys according to the weight_mapping rules.
    Then we load the tensors into the model, applying any conversion operations as needed.

    The `param_name_to_load` will look like this:
    {
        "model.layers.0.attention.q.weight": # Notice here there is only the first key of the target keys
            WeightConverter(
                source_patterns=["qkv"],
                target_patterns=["q", "k","v"],
                operations=[Chunk(dim=0, chunks=3)]),
                collected_tensors={
                    "qkv": [Future]},
                layer_targets={
                    "model.layers.0.attention.q.weight": {"model.layers.0.attention.qkv.weight"},
                    "model.layers.0.attention.k.weight": {"model.layers.0.attention.qkv.weight"},
                    "model.layers.0.attention.v.weight": {"model.layers.0.attention.qkv.weight"},
                }
            ),
        ...
    }

    We make sure that the keys are the full keys. The only "nit" here is that 1 key can map to multiple target keys (e.g. qkv -> q, k, v).
    In that case the weight converter will take care of doing the appropriate renaming.

    For example for:
    ```python
    WeightConverter(
        source_patterns=["mlp.experts.*.gate_proj.weight","mlp.experts.*.up_proj.weight"],
        target_patterns="mlp.experts.gate_up_proj",
        operations=[MergeModulelist(dim=0), Concatenate(dim=1)],
    )
    ```
    we would have the following collected tensors:
    ```python
    collected_tensors = {
        "mlp.experts.*.gate_proj.weight": [Future, Future, Future, Future, Future, Future, Future, Future],
        "mlp.experts.*.up_proj.weight": [Future, Future, Future, Future, Future, Future, Future, Future],
    }
    ```
    The first op, `MergeModulelist`, would stack the 8 tensors of each source but will not "rename" them into the fused target name.
    The second op, `Concatenate`, would then rename the fused tensor into the final target name.

    If we want to split `qkv` we would have:
    ```python
    collected_tensors = {
        "attention.qkv.weight": [Future], # here its the full SOURCE keys.
    }
    ```
    The `Chunk` operation would then split the single tensor into 3 and rename them accordingly and update the collected tensors to:
    ```python
    realized_values = {
        "attention.q.weight": [Tensor],
        "attention.k.weight": [Tensor],
        "attention.v.weight": [Tensor],
    }
    ```

    Now that this is done, we can quantize / dequantize accordingly the collected_tensors.

    For some quantization methods, we need to gather different tensors:

    ```python
    # for "medmekk/llama-3.2-1b-float8-torchao"
    WeightConverter(
        source_patterns=[":qdata", ":scale"],
        target_patterns="",
        operations=[TorchaoDeserialize()],
    )
    ```
    This will collect all tensors that have the same prefix, but end with `:qdata` or `:scale`. This will give us:
    ```python
    all_weight_mapping = {
        "model.layers.13.self_attn.o_proj.weight": WeightConverter(
            source_patterns=[":qdata", ":scale"],
            target_patterns="",
            operations=[TorchaoDeserialize()],
            collected_tensors={
                ":qdata": [Future],
                ":scale": [Future],
            },
        ...
    }
    ```

    """
    prefix = model.base_model_prefix
    tp_plan = tp_plan or {}
    device_map = load_config.device_map or {"": "cpu"}
    hf_quantizer = load_config.hf_quantizer
    dtype = load_config.dtype
    device_mesh = load_config.device_mesh
    disk_offload_folder = load_config.disk_offload_folder
    offload_buffers = load_config.offload_buffers
    dtype_plan = load_config.dtype_plan or {}
    weight_mapping = load_config.weight_mapping or []
    meta_model_state_dict = model.state_dict()
    model_buffers = {k for k, _ in model.named_buffers()}

    # We start from all missing keys, and we will remove/add them from the proper containers as loading advances
    loading_info = LoadStateDictInfo(
        missing_keys=set(meta_model_state_dict.keys()),
        unexpected_keys=set(),
        mismatched_keys=set(),
        conversion_errors={},
        error_msgs=[],
    )

    # We use threading by default, if not explicitly deactivated via env variable. If we have to offload,
    # we cannot use it either to control the memory as we are under memory constraints, so we need to be sequential.
    # When doing on-the-fly quantization, we also use sync loading to avoid worker threads loading full-precision
    # tensors to GPU faster than the main thread can quantize them, which would cause a large memory spike.
    has_on_the_fly_quantization = hf_quantizer is not None and not hf_quantizer.pre_quantized
    if (
        is_env_variable_true("HF_DEACTIVATE_ASYNC_LOAD")
        or "disk" in device_map.values()
        or has_on_the_fly_quantization
    ):
        thread_pool = None
    else:
        thread_pool = ThreadPoolExecutor(max_workers=GLOBAL_WORKERS)

    renamings = [entry for entry in weight_mapping if isinstance(entry, WeightRenaming)]
    converters = [entry for entry in weight_mapping if isinstance(entry, WeightConverter)]
    param_name_to_load: dict[str, WeightRenaming | WeightConverter] = {}

    # build '(?P<g0>.*.*\\.block_sparse_moe\\..*)' and group to source {'g0': '*.block_sparse_moe.'}
    # and target to source {'g0': '*.mlp.'}. This allows us to quickly find which pattern matched.
    if tp_plan != {}:
        tp_plan_alt, tp_plan_by_group_name, _ = build_glob_alternation(list(tp_plan.keys()))
    if dtype_plan != {}:
        dtype_policy_alt, dtype_policy_by_group_name, _ = build_glob_alternation(list(dtype_plan.keys()))

    pattern_to_converter = {k: converter for converter in converters for k in converter.source_patterns}

    state_dict = sorted(state_dict.items(), key=lambda kv: dot_natural_key(kv[0]))
    for original_key, tensor in state_dict:
        # 1. Rename the key according to all renaming pattern and optional weight converter patterns
        renamed_key, source_pattern = rename_source_key(
            original_key, renamings, converters, prefix, meta_model_state_dict
        )
        if renamed_key not in meta_model_state_dict and original_key in meta_model_state_dict:
            # Key should probably not have been renamed but we might need the `prefix` to be added.`
            renamed_key, source_pattern = rename_source_key(original_key, [], [], prefix, meta_model_state_dict)

        # 2. finally, collect the tensor into the proper converter
        if renamed_key in meta_model_state_dict:
            empty_param = meta_model_state_dict.get(renamed_key)
            # If we enter here, we have a WeightConverter operation to perform
            if source_pattern is not None:
                new_converter = deepcopy(pattern_to_converter[source_pattern])
                # each target key gets its own converter instance
                mapping = param_name_to_load.setdefault(renamed_key, new_converter)
            # Otherwise, only potential renaming
            else:
                mapping = param_name_to_load.setdefault(renamed_key, WeightRenaming(original_key, renamed_key))
                source_pattern = original_key

            # 3. Handle dtype casting
            needs_quantization = (
                hf_quantizer
                and not hf_quantizer.pre_quantized
                and hf_quantizer.param_needs_quantization(model, renamed_key)
            )
            if needs_quantization:
                mapping.quantization_operation = hf_quantizer.get_quantize_ops()

            _dtype = dtype
            if (
                hf_quantizer
                and hf_quantizer.pre_quantized
                and (
                    original_key != renamed_key
                    or not (
                        tensor.get_dtype().startswith(("F", "BF"))
                        if hasattr(tensor, "get_dtype")
                        else tensor.is_floating_point()
                    )
                )
            ):
                # if the key was renamed as it is not available in the state dict otherwise, it means that we are deserializing it,
                # so we need to make sure to load the tensor with the same dtype from the checkpoint
                # TODO: make the condition more srict for native fp8 model such as qwen2moe fp8
                _dtype = None
            elif dtype_plan != {} and dtype_policy_alt.search(renamed_key):
                matched_dtype_pattern = dtype_policy_alt.search(renamed_key)
                if matched_dtype_pattern is not None:
                    _dtype = dtype_plan[dtype_policy_by_group_name[matched_dtype_pattern.lastgroup]]
            elif empty_param is not None and empty_param.dtype != _dtype:
                _dtype = empty_param.dtype  # usually correct when initializing

            # 4. Handle TP sharding or device_map placement
            future_or_tensor = None
            if device_mesh and tp_plan:
                if matched_tp_pattern := tp_plan_alt.search(renamed_key):
                    matched_tp_pattern = tp_plan_by_group_name[matched_tp_pattern.lastgroup]
                    if getattr(mapping, "distributed_operation", None) is None:
                        tp_layer = ALL_PARALLEL_STYLES[model.tp_plan[matched_tp_pattern]].__class__
                        mapping.distributed_operation = tp_layer(
                            device_mesh=device_mesh, rank=device_mesh.get_local_rank(), empty_param=empty_param.clone()
                        )
                    shard_index = (
                        len(mapping.collected_tensors.get(source_pattern, []))
                        if isinstance(mapping, WeightConverter) and isinstance(mapping.operations[0], MergeModulelist)
                        else None
                    )
                    future_or_tensor = spawn_tp_materialize(
                        thread_pool,
                        tensor,
                        mapping.distributed_operation,
                        shard_index,
                        device_map[""],
                        _dtype,
                    )

            if future_or_tensor is None:
                param_device = get_device(device_map, renamed_key, valid_torch_device=True)
                future_or_tensor = spawn_materialize(thread_pool, tensor, param_device, _dtype)

            mapping.add_tensor(renamed_key, original_key, source_pattern, future_or_tensor)
        elif source_pattern is not None:  # add all target keys as unexpected
            mapping = pattern_to_converter[source_pattern]
            for k in mapping.target_patterns:
                loading_info.unexpected_keys.add(renamed_key.replace(mapping.target_patterns[0], k))
        else:
            loading_info.unexpected_keys.add(renamed_key)

    try:
        for first_param_name, mapping in tqdm(param_name_to_load.items(), desc="Loading weights"):
            try:
                realized_value = mapping.convert(
                    first_param_name,
                    model=model,
                    config=model.config,
                    hf_quantizer=hf_quantizer,
                    loading_info=loading_info,
                )
                for target_name, param in realized_value.items():
                    param = param[0] if isinstance(param, list) else param
                    param_device = get_device(device_map, target_name)
                    # Offloading support
                    if param_device == "disk" and (target_name not in model_buffers or offload_buffers):
                        disk_offload_index = offload_and_maybe_resave_param(
                            target_name, param, loading_info, disk_offload_folder, disk_offload_index, mapping
                        )
                    else:
                        set_param_for_module(
                            model,
                            target_name,
                            param,
                            loading_info,
                            mapping.distributed_operation,
                            hf_quantizer,
                        )

                # Cleanup all the tensors that were gathered before next iteration
                del realized_value

            except SkipParameters:
                continue

    # Close the pool, independently of whether the code was interrupted or finished successfully
    finally:
        if thread_pool is not None:
            # `cancel_futures=True` in case the program was interrupted, to avoid wasting time on exit
            thread_pool.shutdown(wait=False, cancel_futures=True)

    # Keep the current weight conversion mapping for later saving (in case it was coming directly from the user), but
    # only if it was used, i.e. it matched any weight from the checkpoints
    model_specific_conversions = [conversion for conversion in weight_mapping if conversion.was_used()]
    model._weight_conversions = model_specific_conversions

    return loading_info, disk_offload_index