def download_weights_from_hf(
    model_name_or_path: str,
    cache_dir: str | None,
    allow_patterns: list[str],
    revision: str | None = None,
    subfolder: str | None = None,
    ignore_patterns: str | list[str] | None = None,
) -> str:
    """Download model weights from Hugging Face Hub.

    Args:
        model_name_or_path (str): The model name or path.
        cache_dir (Optional[str]): The cache directory to store the model
            weights. If None, will use HF defaults.
        allow_patterns (list[str]): The allowed patterns for the
            weight files. Files matched by any of the patterns will be
            downloaded.
        revision (Optional[str]): The revision of the model.
        subfolder (Optional[str]): The subfolder within the model repository
            to download weights from.
        ignore_patterns (Optional[Union[str, list[str]]]): The patterns to
            filter out the weight files. Files matched by any of the patterns
            will be ignored.

    Returns:
        str: The path to the downloaded model weights.
    """
    assert len(allow_patterns) > 0
    local_only = huggingface_hub.constants.HF_HUB_OFFLINE
    if not local_only:
        # Attempt to reduce allow_patterns to a single pattern
        # so we only have to call snapshot_download once.
        try:
            fs = HfFileSystem()
            file_list = fs.ls(
                os.path.join(model_name_or_path, subfolder or ""),
                detail=False,
                revision=revision,
            )

            # If downloading safetensors and an index file exists, use the
            # specific file names from the index to avoid downloading
            # unnecessary files (e.g., from subdirectories like "original/").
            index_file = f"{model_name_or_path}/{SAFE_WEIGHTS_INDEX_NAME}"
            if "*.safetensors" in allow_patterns and index_file in file_list:
                index_path = hf_hub_download(
                    repo_id=model_name_or_path,
                    filename=SAFE_WEIGHTS_INDEX_NAME,
                    cache_dir=cache_dir,
                    revision=revision,
                    subfolder=subfolder,
                )
                with open(index_path) as f:
                    weight_map = json.load(f)["weight_map"]
                if weight_map:
                    # Extra [] so that weight_map files are treated as a
                    # single allow_pattern in the loop below
                    allow_patterns = [list(set(weight_map.values()))]  # type: ignore[list-item]
                else:
                    allow_patterns = ["*.safetensors"]
            else:
                # Use the first pattern found in the HF repo's files.
                for pattern in allow_patterns:
                    if fnmatch.filter(file_list, pattern):
                        allow_patterns = [pattern]
                        break
        except Exception as e:
            logger.warning(
                "Failed to get file list for '%s'. Trying each pattern in "
                "allow_patterns individually until weights have been "
                "downloaded. Error: %s",
                model_name_or_path,
                e,
            )

    logger.debug("Using model weights format %s", allow_patterns)
    # Use file lock to prevent multiple processes from
    # downloading the same model weights at the same time.
    with get_lock(model_name_or_path, cache_dir):
        start_time = time.perf_counter()
        for allow_pattern in allow_patterns:
            hf_folder = snapshot_download(
                model_name_or_path,
                allow_patterns=allow_pattern,
                ignore_patterns=ignore_patterns,
                cache_dir=cache_dir,
                tqdm_class=DisabledTqdm,
                revision=revision,
                local_files_only=local_only,
            )
            # If we have downloaded weights for this allow_pattern,
            # we don't need to check the rest.
            # allow_pattern can be a list (from weight_map) or str (glob)
            if isinstance(allow_pattern, list):
                break
            if any(Path(hf_folder).glob(allow_pattern)):
                break
        time_taken = time.perf_counter() - start_time
        if time_taken > 0.5:
            logger.info(
                "Time spent downloading weights for %s: %.6f seconds",
                model_name_or_path,
                time_taken,
            )
    return hf_folder