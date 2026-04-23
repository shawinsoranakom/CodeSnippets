def load_gguf_checkpoint(gguf_checkpoint_path, return_tensors=False, model_to_load=None, torch_dtype=None):
    """
    Load a GGUF file and return a dictionary of parsed parameters containing tensors, the parsed
    tokenizer and config attributes.

    Args:
        gguf_checkpoint_path (`str`):
            The path the to GGUF file to load
        return_tensors (`bool`, defaults to `False`):
            Whether to read the tensors from the file and return them. Not doing so is faster
            and only loads the metadata in memory.
        model_to_load (`nn.Module`, *optional*):
            The model to load the weights into. This is used to map GGUF tensor names to
            Transformers parameter names.
        torch_dtype (`torch.dtype`, *optional*):
            The desired `torch.dtype` for the loaded tensors. If provided, tensors will be
            converted to this dtype immediately after dequantization to save memory.
    """
    if is_gguf_available() and is_torch_available():
        from gguf import GGUFReader, dequantize
    else:
        logger.error(
            "Loading a GGUF checkpoint in PyTorch, requires both PyTorch and GGUF>=0.10.0 to be installed. Please see "
            "https://pytorch.org/ and https://github.com/ggerganov/llama.cpp/tree/master/gguf-py for installation instructions."
        )
        raise ImportError("Please install torch and gguf>=0.10.0 to load a GGUF checkpoint in PyTorch.")

    reader = GGUFReader(gguf_checkpoint_path)
    fields = reader.fields
    reader_keys = list(fields.keys())

    parsed_parameters = {k: {} for k in GGUF_TO_TRANSFORMERS_MAPPING}

    architecture = read_field(reader, "general.architecture")[0]
    # NOTE: Some GGUF checkpoints may miss `general.name` field in metadata
    model_name = read_field(reader, "general.name")

    updated_architecture = None
    # in llama.cpp mistral models use the same architecture as llama. We need
    # to add this patch to ensure things work correctly on our side.
    if "llama" in architecture and "mistral" in model_name:
        updated_architecture = "mistral"
    # FIXME: Currently this implementation is only for flan-t5 architecture.
    # It needs to be developed for supporting legacy t5.
    elif "t5" in architecture or "t5encoder" in architecture:
        parsed_parameters["config"]["is_gated_act"] = True
        if model_name and "umt5" in model_name[0].lower():
            updated_architecture = "umt5"
            if "t5encoder" in architecture:
                parsed_parameters["config"]["architectures"] = ["UMT5EncoderModel"]
        else:
            if "t5encoder" in architecture:
                parsed_parameters["config"]["architectures"] = ["T5EncoderModel"]
            updated_architecture = "t5"
    else:
        updated_architecture = architecture

    if "qwen2moe" in architecture:
        updated_architecture = "qwen2_moe"
    elif "gpt_oss" in architecture or "gpt-oss" in architecture:
        updated_architecture = "gpt_oss"
    elif "qwen3moe" in architecture:
        updated_architecture = "qwen3_moe"
    elif "minimax-m2" in architecture:
        updated_architecture = "minimax_m2"

    # For stablelm architecture, we need to set qkv_bias and use_parallel_residual from tensors
    # If `qkv_bias=True`, qkv_proj with bias will be present in the tensors
    # If `use_parallel_residual=False`, ffn_norm will be present in the tensors
    if "stablelm" in architecture:
        attn_bias_name = {"attn_q.bias", "attn_k.bias", "attn_v.bias"}
        ffn_norm_name = "ffn_norm"
        qkv_bias = any(bias_name in tensor.name for tensor in reader.tensors for bias_name in attn_bias_name)
        use_parallel_residual = any(ffn_norm_name in tensor.name for tensor in reader.tensors)
        parsed_parameters["config"]["use_qkv_bias"] = qkv_bias
        parsed_parameters["config"]["use_parallel_residual"] = not use_parallel_residual

    if architecture not in GGUF_SUPPORTED_ARCHITECTURES and updated_architecture not in GGUF_SUPPORTED_ARCHITECTURES:
        raise ValueError(f"GGUF model with architecture {architecture} is not supported yet.")

    # Handle tie_word_embeddings, if lm_head.weight is not present in tensors,
    # tie_word_embeddings is true otherwise false
    exceptions = ["falcon", "bloom"]
    parsed_parameters["config"]["tie_word_embeddings"] = (
        all(tensor.name != "output.weight" for tensor in reader.tensors) or architecture in exceptions
    )

    # Set GGUF-specific default values
    config_defaults = GGUF_CONFIG_DEFAULTS_MAPPING.get(
        updated_architecture, GGUF_CONFIG_DEFAULTS_MAPPING.get(architecture) or {}
    )
    for key, value in config_defaults.items():
        parsed_parameters["config"].setdefault(key, value)

    # List all key-value pairs in a columnized format
    for gguf_key, field in reader.fields.items():
        gguf_key = gguf_key.replace(architecture, updated_architecture)
        split = gguf_key.split(".")
        prefix = split[0]
        config_key = ".".join(split[1:])

        value = [_gguf_parse_value(field.parts[_data_index], field.types) for _data_index in field.data]

        if len(value) == 1:
            value = value[0]

        if isinstance(value, str) and architecture in value:
            value = value.replace(architecture, updated_architecture)

        for parameter, parameter_renames in GGUF_TO_TRANSFORMERS_MAPPING.items():
            if prefix in parameter_renames and config_key in parameter_renames[prefix]:
                renamed_config_key = parameter_renames[prefix][config_key]
                if renamed_config_key == -1:
                    continue

                if renamed_config_key is not None:
                    parsed_parameters[parameter][renamed_config_key] = value

                if gguf_key in reader_keys:
                    reader_keys.remove(gguf_key)

        if gguf_key in reader_keys:
            logger.info(f"Some keys were not parsed and added into account {gguf_key} | {value}")

    # Gemma3 GGUF checkpoint only contains weights of text backbone
    if parsed_parameters["config"]["model_type"] == "gemma3":
        parsed_parameters["config"]["model_type"] = "gemma3_text"

    # MiniMax-M2: convert expert_gating_func integer to scoring_func string
    if parsed_parameters["config"].get("model_type") == "minimax_m2":
        _gating_func_map = {0: "none", 1: "softmax", 2: "sigmoid"}
        _scoring = parsed_parameters["config"].get("scoring_func")
        if isinstance(_scoring, int):
            parsed_parameters["config"]["scoring_func"] = _gating_func_map.get(_scoring, "softmax")

    if parsed_parameters["config"]["model_type"] == "lfm2":
        gguf_num_key_value_heads = parsed_parameters["config"]["num_key_value_heads"]
        # LFM2 GGUF checkpoint defines num_key_value_heads as a list of integers .e.g [0, 0, 8, 0, 0, 8, 0, 0, 8, 0, 8, 0, 8, 0, 8, 0] but we need to set it to the max value for HF
        parsed_parameters["config"]["num_key_value_heads"] = max(gguf_num_key_value_heads)
        ## we already read the correct intermediate_size from the GGUF checkpoint so we need to set block_auto_adjust_ff_dim to False
        parsed_parameters["config"]["block_auto_adjust_ff_dim"] = False

        ## llama.cpp defines the layers that are full-attention by looking at num_key_value_heads
        ## we need to set the full_attn_idxs to the layers that are full-attention
        parsed_parameters["config"]["full_attn_idxs"] = [
            i for i, num_kv_heads in enumerate(gguf_num_key_value_heads) if num_kv_heads > 0
        ]

    if updated_architecture == "gpt_oss":
        # Helper to read keys with the correct prefix
        def read_gpt_key(reader, suffix, default=None):
            key = f"gpt-oss.{suffix}"
            if key in reader.fields:
                val = reader.fields[key].parts[0]
                if isinstance(val, bytes):
                    val = val.decode("utf-8")
                return val
            return default

        #  Reconstruct rope_scaling from GGUF metadata
        rope_type = read_gpt_key(reader, "rope.scaling.type")
        if rope_type is not None:
            rope_scaling = {"rope_type": rope_type}

            # Collect all rope.scaling keys dynamically
            for key in reader.fields:
                if not key.startswith("gpt-oss.rope.scaling."):
                    continue
                suffix = key[len("gpt-oss.rope.scaling.") :]
                if suffix == "type":
                    continue
                value = reader.fields[key].parts[0]
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                # Convert to appropriate type
                if suffix in ("factor", "attention_factor", "beta_fast", "beta_slow"):
                    value = float(value)
                elif suffix in ("original_context_length", "original_max_position_embeddings"):
                    # Map GGUF's original_context_length to HF's original_max_position_embeddings
                    suffix = "original_max_position_embeddings"
                    value = int(value)
                else:
                    pass
                rope_scaling[suffix] = value

            parsed_parameters["config"]["rope_scaling"] = rope_scaling

    # retrieve config vocab_size from tokenizer
    # Please refer to https://github.com/huggingface/transformers/issues/32526 for more details
    if "vocab_size" not in parsed_parameters["config"]:
        tokenizer_parameters = parsed_parameters["tokenizer"]
        if "tokens" in tokenizer_parameters:
            parsed_parameters["config"]["vocab_size"] = len(tokenizer_parameters["tokens"])
        else:
            logger.warning(
                "Can't find a way to retrieve missing config vocab_size from tokenizer parameters. "
                "This will use default value from model config class and cause unexpected behavior."
            )

    if return_tensors:
        parsed_parameters["tensors"] = {}

        config = parsed_parameters.get("config", {})

        ProcessorClass = TENSOR_PROCESSORS.get(architecture, TensorProcessor)
        processor = ProcessorClass(config=config)

        tensor_key_mapping = get_gguf_hf_weights_map(model_to_load, processor)

        for tensor in tqdm(reader.tensors, desc="Converting and de-quantizing GGUF tensors..."):
            name = tensor.name
            weights = dequantize(tensor.data, tensor.tensor_type)

            result = processor.process(
                weights=weights,
                name=name,
                tensor_key_mapping=tensor_key_mapping,
                parsed_parameters=parsed_parameters,
            )

            weights = result.weights
            name = result.name

            if name not in tensor_key_mapping:
                continue

            name = tensor_key_mapping[name]

            tensor = torch.from_numpy(np.copy(weights))
            if torch_dtype is not None:
                tensor = tensor.to(torch_dtype)
            parsed_parameters["tensors"][name] = tensor

    if len(reader_keys) > 0:
        logger.info(f"Some keys of the GGUF file were not considered: {reader_keys}")

    return parsed_parameters