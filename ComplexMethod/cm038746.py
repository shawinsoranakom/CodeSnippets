def validate_args(args):
    """
    Validate command-line arguments for mm_processor benchmark.
    """
    if not getattr(args, "tokenizer", None):
        args.tokenizer = args.model
    if not hasattr(args, "dataset_path"):
        args.dataset_path = None
    if not hasattr(args, "lora_path"):
        args.lora_path = None
    if not hasattr(args, "max_loras"):
        args.max_loras = None

    if args.dataset_name == "hf" and not args.dataset_path:
        raise ValueError(
            "--dataset-path is required when using --dataset-name hf. "
            "For multimodal benchmarking, specify a dataset like "
            "'lmarena-ai/VisionArena-Chat'."
        )
    if args.dataset_name == "hf":
        supported_mm_datasets = (
            VisionArenaDataset.SUPPORTED_DATASET_PATHS.keys()
            | MultiModalConversationDataset.SUPPORTED_DATASET_PATHS
        )
        if args.dataset_path not in supported_mm_datasets:
            raise ValueError(
                f"{args.dataset_path} is not a supported multimodal dataset. "
                f"Supported multimodal datasets are: {sorted(supported_mm_datasets)}"
            )