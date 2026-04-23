def tensorize_lora_adapter(lora_path: str, tensorizer_config: TensorizerConfig):
    """
    Uses tensorizer to serialize a LoRA adapter. Assumes that the files
    needed to load a LoRA adapter are a safetensors-format file called
    adapter_model.safetensors and a json config file called adapter_config.json.

    Serializes the files in the tensorizer_config.tensorizer_dir
    """
    import safetensors

    from vllm.lora.utils import get_adapter_absolute_path

    lora_dir = get_adapter_absolute_path(lora_path)

    tensor_path = config_path = ""

    for file in os.listdir(lora_dir):
        if file.startswith("adapter_model"):
            tensor_path = lora_dir + "/" + file
        if file.startswith("adapter_config"):
            config_path = lora_dir + "/" + file
        if tensor_path and config_path:
            break

    if tensor_path.endswith(".safetensors"):
        tensors = safetensors.torch.load_file(tensor_path)
    elif tensor_path.endswith(".bin"):
        tensors = torch.load(tensor_path, weights_only=True)
    else:
        raise ValueError(
            f"Unsupported adapter model file: {tensor_path}. "
            f"Must be a .safetensors or .bin file."
        )

    with open(config_path) as f:
        config = json.load(f)

    tensorizer_args = tensorizer_config._construct_tensorizer_args()

    with open_stream(
        f"{tensorizer_config.tensorizer_dir}/adapter_config.json",
        mode="wb+",
        **tensorizer_args.stream_kwargs,
    ) as f:
        f.write(json.dumps(config).encode("utf-8"))

    lora_uri = f"{tensorizer_config.tensorizer_dir}/adapter_model.tensors"
    with open_stream(lora_uri, mode="wb+", **tensorizer_args.stream_kwargs) as f:
        serializer = TensorSerializer(f)
        serializer.write_state_dict(tensors)
        serializer.close()

    logger.info(
        "Successfully serialized LoRA files to %s",
        str(tensorizer_config.tensorizer_dir),
    )