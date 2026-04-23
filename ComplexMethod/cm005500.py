def maybe_load_adapters(
    pretrained_model_name_or_path,
    download_kwargs: DownloadKwargs,
    **adapter_kwargs,
):
    if pretrained_model_name_or_path is None or not is_peft_available():
        return None, pretrained_model_name_or_path, adapter_kwargs

    token = download_kwargs.get("token")

    if download_kwargs.get("commit_hash") is None:
        resolved_config_file = cached_file(
            pretrained_model_name_or_path,
            CONFIG_NAME,
            cache_dir=download_kwargs.get("cache_dir"),
            force_download=bool(download_kwargs.get("force_download", False)),
            proxies=download_kwargs.get("proxies"),
            local_files_only=bool(download_kwargs.get("local_files_only", False)),
            token=token,
            revision=download_kwargs.get("revision"),
            subfolder=download_kwargs.get("subfolder"),
            _raise_exceptions_for_gated_repo=False,
            _raise_exceptions_for_missing_entries=False,
            _raise_exceptions_for_connection_errors=False,
        )
        download_kwargs["commit_hash"] = extract_commit_hash(resolved_config_file, None)

    _adapter_model_path = adapter_kwargs.pop("_adapter_model_path", None)

    token_from_adapter_kwargs = adapter_kwargs.pop("token", None)

    if _adapter_model_path is None:
        peft_kwargs = adapter_kwargs.copy()
        for arg_name in ("cache_dir", "proxies", "subfolder"):  # don't override revision
            if (arg_name not in peft_kwargs) and (arg_name in download_kwargs):
                peft_kwargs[arg_name] = download_kwargs[arg_name]
        if "commit_hash" in download_kwargs:
            peft_kwargs["_commit_hash"] = download_kwargs["commit_hash"]
        peft_kwargs["force_download"] = bool(download_kwargs.get("force_download", False))
        peft_kwargs["local_files_only"] = bool(download_kwargs.get("local_files_only", False))
        peft_kwargs["token"] = token or token_from_adapter_kwargs
        _adapter_model_path = find_adapter_config_file(
            pretrained_model_name_or_path,
            **peft_kwargs,
        )

    if _adapter_model_path is not None and os.path.isfile(_adapter_model_path):
        with open(_adapter_model_path, "r", encoding="utf-8") as f:
            _adapter_model_path = pretrained_model_name_or_path
            # Only override the model name/path if the current value doesn't point to a
            # complete model with an embedded adapter so that local models with embedded
            # adapters will load from the local base model rather than pull the base
            # model named in the adapter's config from the hub.
            if not os.path.exists(pretrained_model_name_or_path) or not os.path.exists(
                os.path.join(pretrained_model_name_or_path, CONFIG_NAME)
            ):
                pretrained_model_name_or_path = json.load(f)["base_model_name_or_path"]

    return _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs