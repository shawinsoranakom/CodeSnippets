def validate_args(args):
    """
    Validate command-line arguments.
    """

    # === Deprecation and Defaulting ===
    if args.dataset is not None:
        warnings.warn(
            "The '--dataset' argument will be deprecated in the next release. "
            "Please use '--dataset-name' and '--dataset-path' instead.",
            stacklevel=2,
        )
        args.dataset_path = args.dataset

    if not getattr(args, "tokenizer", None):
        args.tokenizer = args.model

    # === Backend Validation ===
    valid_backends = {"vllm", "hf", "mii", "vllm-chat"}
    if args.backend not in valid_backends:
        raise ValueError(f"Unsupported backend: {args.backend}")

    # === Dataset Configuration ===
    if (
        not args.dataset
        and not args.dataset_path
        and args.dataset_name not in {"prefix_repetition"}
    ):
        print("When dataset path is not set, it will default to random dataset")
        args.dataset_name = "random"
        random_input_len = getattr(args, "random_input_len", None)
        if args.input_len is None and random_input_len is None:
            raise ValueError(
                "Either --input-len or --random-input-len must be provided "
                "for a random dataset"
            )

    # === Dataset Name Specific Checks ===
    # --hf-subset and --hf-split: only used
    # when dataset_name is 'hf'
    if args.dataset_name != "hf" and (
        getattr(args, "hf_subset", None) is not None
        or getattr(args, "hf_split", None) is not None
    ):
        warnings.warn(
            "--hf-subset and --hf-split will be ignored \
                since --dataset-name is not 'hf'.",
            stacklevel=2,
        )
    elif args.dataset_name == "hf":
        if args.dataset_path in (
            VisionArenaDataset.SUPPORTED_DATASET_PATHS.keys()
            | MultiModalConversationDataset.SUPPORTED_DATASET_PATHS
            | ConversationDataset.SUPPORTED_DATASET_PATHS
        ):
            assert args.backend == "vllm-chat", (
                f"{args.dataset_path} needs to use vllm-chat as the backend."
            )
        elif args.dataset_path in (
            InstructCoderDataset.SUPPORTED_DATASET_PATHS
            | AIMODataset.SUPPORTED_DATASET_PATHS
            | ASRDataset.SUPPORTED_DATASET_PATHS
        ):
            assert args.backend == "vllm", (
                f"{args.dataset_path} needs to use vllm as the backend."
            )
        else:
            raise ValueError(f"{args.dataset_path} is not supported by hf dataset.")

    # --random-range-ratio: only used when dataset_name is 'random',
    # 'random-mm', or 'random-rerank'
    if (
        args.dataset_name not in {"random", "random-mm", "random-rerank"}
        and args.random_range_ratio is not None
    ):
        warnings.warn(
            "--random-range-ratio will be ignored since \
                --dataset-name is not 'random', 'random-mm', or 'random-rerank'.",
            stacklevel=2,
        )

    # --random-batch-size: only used when dataset_name is 'random-rerank'
    if (
        args.dataset_name != "random-rerank"
        and getattr(args, "random_batch_size", None) is not None
    ) and args.random_batch_size != 1:
        warnings.warn(
            "--random-batch-size will be ignored since \
                    --dataset-name is not 'random-rerank'.",
            stacklevel=2,
        )

    # --no-reranker: only used when dataset_name is 'random-rerank'
    if args.dataset_name != "random-rerank" and getattr(args, "no_reranker", False):
        warnings.warn(
            "--no-reranker will be ignored since \
                --dataset-name is not 'random-rerank'.",
            stacklevel=2,
        )

    # --prefix-len: only used when dataset_name is 'random', 'random-mm',
    # 'sonnet', or not set.
    if (
        args.dataset_name not in {"random", "random-mm", "sonnet", None}
        and args.prefix_len is not None
    ):
        warnings.warn(
            "--prefix-len will be ignored since --dataset-name\
                 is not 'random', 'random-mm', 'sonnet', or not set.",
            stacklevel=2,
        )

    # === Random Dataset Argument Conflict Detection ===
    # Check for conflicts between regular and random arguments when using
    # random datasets
    if args.dataset_name in {"random", "random-mm", "random-rerank"}:
        random_input_len = getattr(args, "random_input_len", None)
        random_output_len = getattr(args, "random_output_len", None)
        random_prefix_len = getattr(args, "random_prefix_len", None)

        if args.input_len is not None and random_input_len is not None:
            warnings.warn(
                "Both --input-len and --random-input-len are specified. "
                "The random version (--random-input-len) will be preferred "
                "in this run.",
                stacklevel=2,
            )
        if args.output_len is not None and random_output_len is not None:
            warnings.warn(
                "Both --output-len and --random-output-len are specified. "
                "The random version (--random-output-len) will be preferred "
                "in this run.",
                stacklevel=2,
            )
        if args.prefix_len is not None and random_prefix_len is not None:
            warnings.warn(
                "Both --prefix-len and --random-prefix-len are specified. "
                "The random version (--random-prefix-len) will be preferred "
                "in this run.",
                stacklevel=2,
            )

    # === LoRA Settings ===
    if getattr(args, "enable_lora", False) and args.backend != "vllm":
        raise ValueError("LoRA benchmarking is only supported for vLLM backend")
    if getattr(args, "enable_lora", False) and args.lora_path is None:
        raise ValueError("LoRA path must be provided when enable_lora is True")

    # === Backend-specific Validations ===
    if args.backend == "hf" and args.hf_max_batch_size is None:
        raise ValueError("HF max batch size is required for HF backend")
    if args.backend != "hf" and args.hf_max_batch_size is not None:
        raise ValueError("HF max batch size is only for HF backend.")

    if (
        args.backend in {"hf", "mii"}
        and getattr(args, "quantization", None) is not None
    ):
        raise ValueError("Quantization is only for vLLM backend.")

    if args.backend == "mii" and args.dtype != "auto":
        raise ValueError("dtype must be auto for MII backend.")
    if args.backend == "mii" and args.n != 1:
        raise ValueError("n must be 1 for MII backend.")
    if args.backend == "mii" and args.tokenizer != args.model:
        raise ValueError("Tokenizer must be the same as the model for MII backend.")

    if args.data_parallel_size > 1 and (
        args.distributed_executor_backend != "external_launcher" or args.async_engine
    ):
        # --data-parallel is not supported fully.
        # Old issue: https://github.com/vllm-project/vllm/issues/16222
        # Currently we only support data parallel with external launcher
        # mode (i.e., launch with toruchrun).
        raise ValueError(
            "Data parallel is only supported with external launcher mode "
            "with synchronous engine in offline benchmark, "
            "please use benchmark serving instead"
        )