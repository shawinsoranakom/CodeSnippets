def get_video_processor_config(
    pretrained_model_name_or_path: str | os.PathLike,
    cache_dir: str | os.PathLike | None = None,
    force_download: bool = False,
    proxies: dict[str, str] | None = None,
    token: bool | str | None = None,
    revision: str | None = None,
    local_files_only: bool = False,
    **kwargs,
):
    """
    Loads the video processor configuration from a pretrained model video processor configuration.

    Args:
        pretrained_model_name_or_path (`str` or `os.PathLike`):
            This can be either:

            - a string, the *model id* of a pretrained model configuration hosted inside a model repo on
              huggingface.co.
            - a path to a *directory* containing a configuration file saved using the
              [`~BaseVideoProcessor.save_pretrained`] method, e.g., `./my_model_directory/`.

        cache_dir (`str` or `os.PathLike`, *optional*):
            Path to a directory in which a downloaded pretrained model configuration should be cached if the standard
            cache should not be used.
        force_download (`bool`, *optional*, defaults to `False`):
            Whether or not to force to (re-)download the configuration files and override the cached versions if they
            exist.
        proxies (`dict[str, str]`, *optional*):
            A dictionary of proxy servers to use by protocol or endpoint, e.g., `{'http': 'foo.bar:3128',
            'http://hostname': 'foo.bar:4012'}.` The proxies are used on each request.
        token (`str` or *bool*, *optional*):
            The token to use as HTTP bearer authorization for remote files. If `True`, will use the token generated
            when running `hf auth login` (stored in `~/.huggingface`).
        revision (`str`, *optional*, defaults to `"main"`):
            The specific model version to use. It can be a branch name, a tag name, or a commit id, since we use a
            git-based system for storing models and other artifacts on huggingface.co, so `revision` can be any
            identifier allowed by git.
        local_files_only (`bool`, *optional*, defaults to `False`):
            If `True`, will only try to load the video processor configuration from local files.

    <Tip>

    Passing `token=True` is required when you want to use a private model.

    </Tip>

    Returns:
        `Dict`: The configuration of the video processor.

    Examples:

    ```python
    # Download configuration from huggingface.co and cache.
    video_processor_config = get_video_processor_config("llava-hf/llava-onevision-qwen2-0.5b-ov-hf")
    # This model does not have a video processor config so the result will be an empty dict.
    video_processor_config = get_video_processor_config("FacebookAI/xlm-roberta-base")

    # Save a pretrained video processor locally and you can reload its config
    from transformers import AutoVideoProcessor

    video_processor = AutoVideoProcessor.from_pretrained("llava-hf/llava-onevision-qwen2-0.5b-ov-hf")
    video_processor.save_pretrained("video-processor-test")
    video_processor = get_video_processor_config("video-processor-test")
    ```"""
    # Load with a priority given to the nested processor config, if available in repo
    resolved_processor_file = cached_file(
        pretrained_model_name_or_path,
        filename=PROCESSOR_NAME,
        cache_dir=cache_dir,
        force_download=force_download,
        proxies=proxies,
        token=token,
        revision=revision,
        local_files_only=local_files_only,
        _raise_exceptions_for_gated_repo=False,
        _raise_exceptions_for_missing_entries=False,
    )
    resolved_video_processor_files = [
        resolved_file
        for filename in [VIDEO_PROCESSOR_NAME, IMAGE_PROCESSOR_NAME]
        if (
            resolved_file := cached_file(
                pretrained_model_name_or_path,
                filename=filename,
                cache_dir=cache_dir,
                force_download=force_download,
                proxies=proxies,
                token=token,
                revision=revision,
                local_files_only=local_files_only,
                _raise_exceptions_for_gated_repo=False,
                _raise_exceptions_for_missing_entries=False,
                _raise_exceptions_for_connection_errors=False,
            )
        )
        is not None
    ]
    resolved_video_processor_file = resolved_video_processor_files[0] if resolved_video_processor_files else None

    # An empty list if none of the possible files is found in the repo
    if not resolved_video_processor_file and not resolved_processor_file:
        logger.info("Could not locate the video processor configuration file.")
        return {}

    # Load video_processor dict. Priority goes as (nested config if found -> video processor config -> image processor config)
    # We are downloading both configs because almost all models have a `processor_config.json` but
    # not all of these are nested. We need to check if it was saved recebtly as nested or if it is legacy style
    video_processor_dict = {}
    if resolved_processor_file is not None:
        processor_dict = safe_load_json_file(resolved_processor_file)
        if "video_processor" in processor_dict:
            video_processor_dict = processor_dict["video_processor"]

    if resolved_video_processor_file is not None and video_processor_dict is None:
        video_processor_dict = safe_load_json_file(resolved_video_processor_file)

    return video_processor_dict