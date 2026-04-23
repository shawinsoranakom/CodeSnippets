def resolve_tokenizer_args(
    tokenizer_name: str | Path,
    *args,
    runner_type: "RunnerType" = "generate",
    tokenizer_mode: str = "auto",
    **kwargs,
):
    revision: str | None = kwargs.get("revision")
    download_dir: str | None = kwargs.get("download_dir")

    if envs.VLLM_USE_MODELSCOPE:
        # download model from ModelScope hub,
        # lazy import so that modelscope is not required for normal use.
        from modelscope.hub.snapshot_download import snapshot_download

        # avoid circular import
        from vllm.model_executor.model_loader.weight_utils import get_lock

        # Only set the tokenizer here, model will be downloaded on the workers.
        if not Path(tokenizer_name).exists():
            # Use file lock to prevent multiple processes from
            # downloading the same file at the same time.
            with get_lock(tokenizer_name, download_dir):
                tokenizer_path = snapshot_download(
                    model_id=str(tokenizer_name),
                    cache_dir=download_dir,
                    revision=revision,
                    local_files_only=huggingface_hub.constants.HF_HUB_OFFLINE,
                    # Ignore weights - we only need the tokenizer.
                    ignore_file_pattern=[".*.pt", ".*.safetensors", ".*.bin"],
                )
                tokenizer_name = tokenizer_path

    # Separate model folder from file path for GGUF models
    if is_gguf(tokenizer_name):
        if check_gguf_file(tokenizer_name):
            kwargs["gguf_file"] = Path(tokenizer_name).name
            tokenizer_name = Path(tokenizer_name).parent
        elif is_remote_gguf(tokenizer_name):
            tokenizer_name, quant_type = split_remote_gguf(tokenizer_name)
            # Get the HuggingFace Hub path for the GGUF file
            gguf_file = get_gguf_file_path_from_hf(
                tokenizer_name,
                quant_type,
                revision=revision,
            )
            kwargs["gguf_file"] = gguf_file

    if "truncation_side" not in kwargs:
        if runner_type == "generate" or runner_type == "draft":
            kwargs["truncation_side"] = "left"
        elif runner_type == "pooling":
            kwargs["truncation_side"] = "right"
        else:
            assert_never(runner_type)

    if tokenizer_mode == "slow":
        if kwargs.get("use_fast", False):
            raise ValueError("Cannot use the fast tokenizer in slow tokenizer mode.")

        tokenizer_mode = "hf"
        kwargs["use_fast"] = False

    # Try to use official Mistral tokenizer if possible
    if (
        tokenizer_mode == "auto"
        and is_mistral_model_repo(
            model_name_or_path=str(tokenizer_name), revision=revision
        )
        and any_pattern_in_repo_files(
            model_name_or_path=str(tokenizer_name),
            allow_patterns=["tekken.json", "tokenizer.model.v*"],
            revision=revision,
        )
    ):
        tokenizer_mode = "mistral"

    # Fallback to HF tokenizer
    if tokenizer_mode == "auto":
        tokenizer_mode = "hf"

    return tokenizer_mode, tokenizer_name, args, kwargs