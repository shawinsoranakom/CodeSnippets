def get_requests(args, tokenizer):
    # Common parameters for all dataset types.
    common_kwargs = {
        "dataset_path": args.dataset_path,
        "random_seed": args.seed,
    }
    sample_kwargs = {
        "tokenizer": tokenizer,
        "lora_path": args.lora_path,
        "max_loras": args.max_loras,
        "lora_assignment": getattr(args, "lora_assignment", "random"),
        "num_requests": args.num_prompts,
    }

    if args.dataset_name == "random" or (
        args.dataset_path is None
        and args.dataset_name not in {"prefix_repetition", "random-mm", "random-rerank"}
    ):
        sample_kwargs["range_ratio"] = args.random_range_ratio
        # prefer random_* arguments, fall back to regular arguments
        random_prefix_len = getattr(args, "random_prefix_len", None)
        sample_kwargs["prefix_len"] = (
            random_prefix_len if random_prefix_len is not None else args.prefix_len
        )
        random_input_len = getattr(args, "random_input_len", None)
        sample_kwargs["input_len"] = (
            random_input_len if random_input_len is not None else args.input_len
        )
        random_output_len = getattr(args, "random_output_len", None)
        sample_kwargs["output_len"] = (
            random_output_len if random_output_len is not None else args.output_len
        )
        dataset_cls = RandomDataset
    elif args.dataset_name == "sharegpt":
        dataset_cls = ShareGPTDataset
        if args.backend == "vllm-chat":
            sample_kwargs["enable_multimodal_chat"] = True
        if args.output_len is not None:
            sample_kwargs["output_len"] = args.output_len
    elif args.dataset_name == "sonnet":
        assert tokenizer.chat_template or tokenizer.default_chat_template, (
            "Tokenizer/model must have chat template for sonnet dataset."
        )
        dataset_cls = SonnetDataset
        sample_kwargs["prefix_len"] = args.prefix_len
        sample_kwargs["return_prompt_formatted"] = True
        if args.input_len is not None:
            sample_kwargs["input_len"] = args.input_len
        if args.output_len is not None:
            sample_kwargs["output_len"] = args.output_len
    elif args.dataset_name == "burstgpt":
        dataset_cls = BurstGPTDataset
    elif args.dataset_name == "hf":
        if args.output_len is not None:
            sample_kwargs["output_len"] = args.output_len
        if args.dataset_path in VisionArenaDataset.SUPPORTED_DATASET_PATHS:
            dataset_cls = VisionArenaDataset
            common_kwargs["dataset_subset"] = None
            common_kwargs["dataset_split"] = "train"
            sample_kwargs["enable_multimodal_chat"] = True
        elif args.dataset_path in InstructCoderDataset.SUPPORTED_DATASET_PATHS:
            dataset_cls = InstructCoderDataset
            common_kwargs["dataset_split"] = "train"
        elif args.dataset_path in MultiModalConversationDataset.SUPPORTED_DATASET_PATHS:
            dataset_cls = MultiModalConversationDataset
            common_kwargs["dataset_subset"] = args.hf_subset
            common_kwargs["dataset_split"] = args.hf_split
            sample_kwargs["enable_multimodal_chat"] = True
        elif args.dataset_path in ConversationDataset.SUPPORTED_DATASET_PATHS:
            dataset_cls = ConversationDataset
            common_kwargs["dataset_subset"] = args.hf_subset
            common_kwargs["dataset_split"] = args.hf_split
            sample_kwargs["enable_multimodal_chat"] = True
        elif args.dataset_path in AIMODataset.SUPPORTED_DATASET_PATHS:
            dataset_cls = AIMODataset
            common_kwargs["dataset_subset"] = None
            common_kwargs["dataset_split"] = "train"
        elif args.dataset_path in ASRDataset.SUPPORTED_DATASET_PATHS:
            dataset_cls = ASRDataset
            common_kwargs["dataset_subset"] = args.hf_subset
            common_kwargs["dataset_split"] = args.hf_split
            sample_kwargs["asr_min_audio_len_sec"] = args.asr_min_audio_len_sec
            sample_kwargs["asr_max_audio_len_sec"] = args.asr_max_audio_len_sec
    elif args.dataset_name == "prefix_repetition":
        dataset_cls = PrefixRepetitionRandomDataset
        sample_kwargs["prefix_len"] = args.prefix_repetition_prefix_len
        sample_kwargs["suffix_len"] = args.prefix_repetition_suffix_len
        sample_kwargs["num_prefixes"] = args.prefix_repetition_num_prefixes
        sample_kwargs["output_len"] = args.prefix_repetition_output_len
    elif args.dataset_name == "random-mm":
        dataset_cls = RandomMultiModalDataset
        # prefer random_* arguments, fall back to regular arguments
        random_input_len = getattr(args, "random_input_len", None)
        sample_kwargs["input_len"] = (
            random_input_len
            if random_input_len is not None
            else getattr(args, "input_len", None)
        )
        random_output_len = getattr(args, "random_output_len", None)
        sample_kwargs["output_len"] = (
            random_output_len
            if random_output_len is not None
            else getattr(args, "output_len", None)
        )
        sample_kwargs["base_items_per_request"] = getattr(
            args, "random_mm_base_items_per_request", None
        )
        sample_kwargs["num_mm_items_range_ratio"] = getattr(
            args, "random_mm_num_mm_items_range_ratio", None
        )
        sample_kwargs["limit_mm_per_prompt"] = getattr(
            args, "random_mm_limit_mm_per_prompt", None
        )
        sample_kwargs["bucket_config"] = getattr(args, "random_mm_bucket_config", None)
        sample_kwargs["enable_multimodal_chat"] = True
        random_prefix_len = getattr(args, "random_prefix_len", None)
        prefix_len = getattr(args, "prefix_len", None)
        sample_kwargs["prefix_len"] = (
            random_prefix_len if random_prefix_len is not None else prefix_len
        )
        sample_kwargs["range_ratio"] = args.random_range_ratio
    elif args.dataset_name == "random-rerank":
        dataset_cls = RandomDatasetForReranking
        # prefer random_* arguments, fall back to regular arguments
        random_input_len = getattr(args, "random_input_len", None)
        sample_kwargs["input_len"] = (
            random_input_len
            if random_input_len is not None
            else getattr(args, "input_len", None)
        )
        random_output_len = getattr(args, "random_output_len", None)
        sample_kwargs["output_len"] = (
            random_output_len
            if random_output_len is not None
            else getattr(args, "output_len", None)
        )
        sample_kwargs["batchsize"] = getattr(args, "random_batch_size", 1)
        sample_kwargs["is_reranker"] = not getattr(args, "no_reranker", False)
        sample_kwargs["range_ratio"] = args.random_range_ratio
    else:
        raise ValueError(f"Unknown dataset name: {args.dataset_name}")
    # Remove None values
    sample_kwargs = {k: v for k, v in sample_kwargs.items() if v is not None}
    requests = dataset_cls(**common_kwargs).sample(**sample_kwargs)
    requests = filter_requests_for_dp(requests, args.data_parallel_size)
    return requests