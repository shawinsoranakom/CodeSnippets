def main():
    parser = get_parser()
    args = parser.parse_args()

    s3_access_key_id = getattr(args, "s3_access_key_id", None) or os.environ.get(
        "S3_ACCESS_KEY_ID", None
    )
    s3_secret_access_key = getattr(
        args, "s3_secret_access_key", None
    ) or os.environ.get("S3_SECRET_ACCESS_KEY", None)
    s3_endpoint = getattr(args, "s3_endpoint", None) or os.environ.get(
        "S3_ENDPOINT_URL", None
    )

    credentials = {
        "s3_access_key_id": s3_access_key_id,
        "s3_secret_access_key": s3_secret_access_key,
        "s3_endpoint": s3_endpoint,
    }

    model_ref = args.model

    if args.command == "serialize" or args.command == "deserialize":
        keyfile = args.keyfile
    else:
        keyfile = None

    extra_config = {}
    if args.model_loader_extra_config:
        extra_config = json.loads(args.model_loader_extra_config)

    tensorizer_dir = args.serialized_directory or extra_config.get("tensorizer_dir")
    tensorizer_uri = getattr(args, "path_to_tensors", None) or extra_config.get(
        "tensorizer_uri"
    )

    if tensorizer_dir and tensorizer_uri:
        parser.error(
            "--serialized-directory and --path-to-tensors cannot both be provided"
        )

    if not tensorizer_dir and not tensorizer_uri:
        parser.error(
            "Either --serialized-directory or --path-to-tensors must be provided"
        )

    if args.command == "serialize":
        engine_args = EngineArgs.from_cli_args(args)

        input_dir = tensorizer_dir.rstrip("/")
        suffix = args.suffix if args.suffix else uuid.uuid4().hex
        base_path = f"{input_dir}/vllm/{model_ref}/{suffix}"
        if engine_args.tensor_parallel_size > 1:
            model_path = f"{base_path}/model-rank-%03d.tensors"
        else:
            model_path = f"{base_path}/model.tensors"

        tensorizer_config = TensorizerConfig(
            tensorizer_uri=model_path,
            encryption_keyfile=keyfile,
            serialization_kwargs=args.serialization_kwargs or {},
            **credentials,
        )

        if args.lora_path:
            tensorizer_config.lora_dir = tensorizer_config.tensorizer_dir
            tensorize_lora_adapter(args.lora_path, tensorizer_config)

        merge_extra_config_with_tensorizer_config(extra_config, tensorizer_config)
        tensorize_vllm_model(engine_args, tensorizer_config)

    elif args.command == "deserialize":
        tensorizer_config = TensorizerConfig(
            tensorizer_uri=args.path_to_tensors,
            tensorizer_dir=args.serialized_directory,
            encryption_keyfile=keyfile,
            deserialization_kwargs=args.deserialization_kwargs or {},
            **credentials,
        )

        merge_extra_config_with_tensorizer_config(extra_config, tensorizer_config)
        deserialize(args, tensorizer_config)
    else:
        raise ValueError("Either serialize or deserialize must be specified.")