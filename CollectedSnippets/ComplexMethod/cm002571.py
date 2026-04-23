def _get_resolved_checkpoint_files(
    pretrained_model_name_or_path: str | os.PathLike | None,
    variant: str | None,
    gguf_file: str | None,
    use_safetensors: bool | None,
    user_agent: dict | None,
    is_remote_code: bool,  # Because we can't determine this inside this function, we need it to be passed in
    transformers_explicit_filename: str | None = None,
    download_kwargs: DownloadKwargs | None = None,
    tqdm_class: type | None = None,
) -> tuple[list[str] | None, dict | None]:
    """Get all the checkpoint filenames based on `pretrained_model_name_or_path`, and optional metadata if the
    checkpoints are sharded.
    This function will download the data if necessary.
    """
    download_kwargs = download_kwargs or DownloadKwargs()
    cache_dir = download_kwargs.get("cache_dir")
    force_download = download_kwargs.get("force_download", False)
    proxies = download_kwargs.get("proxies")
    local_files_only = download_kwargs.get("local_files_only", False)
    token = download_kwargs.get("token")
    revision = download_kwargs.get("revision") or "main"
    subfolder = download_kwargs.get("subfolder", "")
    commit_hash = download_kwargs.get("commit_hash")
    if transformers_explicit_filename is not None:
        if not transformers_explicit_filename.endswith(".safetensors") and not transformers_explicit_filename.endswith(
            ".safetensors.index.json"
        ):
            if transformers_explicit_filename != "adapter_model.bin":
                raise ValueError(
                    "The transformers file in the config seems to be incorrect: it is neither a safetensors file "
                    "(*.safetensors) nor a safetensors index file (*.safetensors.index.json): "
                    f"{transformers_explicit_filename}"
                )

    is_sharded = False

    if pretrained_model_name_or_path is not None and gguf_file is None:
        pretrained_model_name_or_path = str(pretrained_model_name_or_path)
        is_local = os.path.isdir(pretrained_model_name_or_path)
        # If the file is a local folder (but not in the HF_HOME cache, even if it's technically local)
        if is_local:
            if transformers_explicit_filename is not None:
                # If the filename is explicitly defined, load this by default.
                archive_file = os.path.join(pretrained_model_name_or_path, subfolder, transformers_explicit_filename)
                is_sharded = transformers_explicit_filename.endswith(".safetensors.index.json")
            elif use_safetensors is not False and os.path.isfile(
                os.path.join(pretrained_model_name_or_path, subfolder, _add_variant(SAFE_WEIGHTS_NAME, variant))
            ):
                # Load from a safetensors checkpoint
                archive_file = os.path.join(
                    pretrained_model_name_or_path, subfolder, _add_variant(SAFE_WEIGHTS_NAME, variant)
                )
            elif use_safetensors is not False and os.path.isfile(
                os.path.join(pretrained_model_name_or_path, subfolder, _add_variant(SAFE_WEIGHTS_INDEX_NAME, variant))
            ):
                # Load from a sharded safetensors checkpoint
                archive_file = os.path.join(
                    pretrained_model_name_or_path, subfolder, _add_variant(SAFE_WEIGHTS_INDEX_NAME, variant)
                )
                is_sharded = True
            elif not use_safetensors and os.path.isfile(
                os.path.join(pretrained_model_name_or_path, subfolder, _add_variant(WEIGHTS_NAME, variant))
            ):
                # Load from a PyTorch checkpoint
                archive_file = os.path.join(
                    pretrained_model_name_or_path, subfolder, _add_variant(WEIGHTS_NAME, variant)
                )
            elif not use_safetensors and os.path.isfile(
                os.path.join(pretrained_model_name_or_path, subfolder, _add_variant(WEIGHTS_INDEX_NAME, variant))
            ):
                # Load from a sharded PyTorch checkpoint
                archive_file = os.path.join(
                    pretrained_model_name_or_path, subfolder, _add_variant(WEIGHTS_INDEX_NAME, variant)
                )
                is_sharded = True
            elif use_safetensors:
                raise OSError(
                    f"Error no file named {_add_variant(SAFE_WEIGHTS_NAME, variant)} found in directory"
                    f" {pretrained_model_name_or_path}."
                )
            else:
                raise OSError(
                    f"Error no file named {_add_variant(SAFE_WEIGHTS_NAME, variant)}, or {_add_variant(WEIGHTS_NAME, variant)},"
                    f" found in directory {pretrained_model_name_or_path}."
                )
        elif os.path.isfile(os.path.join(subfolder, pretrained_model_name_or_path)):
            archive_file = pretrained_model_name_or_path
            is_local = True
        else:
            # set correct filename
            if transformers_explicit_filename is not None:
                filename = transformers_explicit_filename
                is_sharded = transformers_explicit_filename.endswith(".safetensors.index.json")
            elif use_safetensors is not False:
                filename = _add_variant(SAFE_WEIGHTS_NAME, variant)
            else:
                filename = _add_variant(WEIGHTS_NAME, variant)

            # Prepare set of kwargs for hub functions
            has_file_kwargs = {
                "revision": revision,
                "proxies": proxies,
                "token": token,
                "cache_dir": cache_dir,
                "local_files_only": local_files_only,
            }
            cached_file_kwargs = {
                "force_download": force_download,
                "user_agent": user_agent,
                "subfolder": subfolder,
                "_raise_exceptions_for_gated_repo": False,
                "_raise_exceptions_for_missing_entries": False,
                "_commit_hash": commit_hash,
                "tqdm_class": tqdm_class,
                **has_file_kwargs,
            }
            can_auto_convert = (
                not is_offline_mode()  # for obvious reasons
                # If we are in a CI environment or in a pytest run, we prevent the conversion
                and not is_env_variable_true("DISABLE_SAFETENSORS_CONVERSION")
                and not is_remote_code  # converter bot does not work on remote code
                and subfolder == ""  # converter bot does not work on subfolders
            )

            try:
                # Load from URL or cache if already cached
                # Since we set _raise_exceptions_for_missing_entries=False, we don't get an exception but a None
                # result when internet is up, the repo and revision exist, but the file does not.
                resolved_archive_file = cached_file(pretrained_model_name_or_path, filename, **cached_file_kwargs)

                # Try safetensors files first if not already found
                if resolved_archive_file is None and filename == _add_variant(SAFE_WEIGHTS_NAME, variant):
                    # Maybe the checkpoint is sharded, we try to grab the index name in this case.
                    resolved_archive_file = cached_file(
                        pretrained_model_name_or_path,
                        _add_variant(SAFE_WEIGHTS_INDEX_NAME, variant),
                        **cached_file_kwargs,
                    )
                    if resolved_archive_file is not None:
                        is_sharded = True
                    elif use_safetensors:
                        if revision == "main" and can_auto_convert:
                            resolved_archive_file, revision, is_sharded = auto_conversion(
                                pretrained_model_name_or_path, **cached_file_kwargs
                            )
                        cached_file_kwargs["revision"] = revision
                        if resolved_archive_file is None:
                            raise OSError(
                                f"{pretrained_model_name_or_path} does not appear to have a file named"
                                f" {_add_variant(SAFE_WEIGHTS_NAME, variant)} or {_add_variant(SAFE_WEIGHTS_INDEX_NAME, variant)} "
                                "and thus cannot be loaded with `safetensors`. Please do not set `use_safetensors=True`."
                            )
                    else:
                        # This repo has no safetensors file of any kind, we switch to PyTorch.
                        filename = _add_variant(WEIGHTS_NAME, variant)
                        resolved_archive_file = cached_file(
                            pretrained_model_name_or_path, filename, **cached_file_kwargs
                        )

                # Then try `.bin` files
                if resolved_archive_file is None and filename == _add_variant(WEIGHTS_NAME, variant):
                    # Maybe the checkpoint is sharded, we try to grab the index name in this case.
                    resolved_archive_file = cached_file(
                        pretrained_model_name_or_path,
                        _add_variant(WEIGHTS_INDEX_NAME, variant),
                        **cached_file_kwargs,
                    )
                    if resolved_archive_file is not None:
                        is_sharded = True

                # If we have a match, but it's `.bin` format, try to launch safetensors conversion for next time
                if resolved_archive_file is not None:
                    safe_weights_name = SAFE_WEIGHTS_INDEX_NAME if is_sharded else SAFE_WEIGHTS_NAME
                    if (
                        filename in [WEIGHTS_NAME, WEIGHTS_INDEX_NAME]
                        and not has_file(pretrained_model_name_or_path, safe_weights_name, **has_file_kwargs)
                        and can_auto_convert
                    ):
                        Thread(
                            target=auto_conversion,
                            args=(pretrained_model_name_or_path,),
                            kwargs={"ignore_errors_during_conversion": False, **cached_file_kwargs},
                            name="Thread-auto_conversion",
                        ).start()

                # If no match, raise appropriare errors
                else:
                    # Otherwise, no PyTorch file was found
                    if variant is not None and has_file(
                        pretrained_model_name_or_path, WEIGHTS_NAME, **has_file_kwargs
                    ):
                        raise OSError(
                            f"{pretrained_model_name_or_path} does not appear to have a file named"
                            f" {_add_variant(WEIGHTS_NAME, variant)} but there is a file without the variant"
                            f" {variant}. Use `variant=None` to load this model from those weights."
                        )
                    else:
                        raise OSError(
                            f"{pretrained_model_name_or_path} does not appear to have a file named"
                            f" {_add_variant(WEIGHTS_NAME, variant)} or {_add_variant(SAFE_WEIGHTS_NAME, variant)}."
                        )

            except OSError:
                # Raise any environment error raise by `cached_file`. It will have a helpful error message adapted
                # to the original exception.
                raise
            except Exception as e:
                # For any other exception, we throw a generic error.
                raise OSError(
                    f"Can't load the model for '{pretrained_model_name_or_path}'. If you were trying to load it"
                    " from 'https://huggingface.co/models', make sure you don't have a local directory with the"
                    f" same name. Otherwise, make sure '{pretrained_model_name_or_path}' is the correct path to a"
                    f" directory containing a file named {_add_variant(WEIGHTS_NAME, variant)}."
                ) from e

        if is_local:
            logger.info(f"loading weights file {archive_file}")
            resolved_archive_file = archive_file
        else:
            logger.info(f"loading weights file {filename} from cache at {resolved_archive_file}")

    elif gguf_file:
        # Case 1: the GGUF file is present locally
        if os.path.isfile(gguf_file):
            resolved_archive_file = gguf_file
        # Case 2: The GGUF path is a location on the Hub
        # Load from URL or cache if already cached
        else:
            cached_file_kwargs = {
                "cache_dir": cache_dir,
                "force_download": force_download,
                "proxies": proxies,
                "local_files_only": local_files_only,
                "token": token,
                "user_agent": user_agent,
                "revision": revision,
                "subfolder": subfolder,
                "_raise_exceptions_for_gated_repo": False,
                "_raise_exceptions_for_missing_entries": False,
                "_commit_hash": commit_hash,
            }

            resolved_archive_file = cached_file(pretrained_model_name_or_path, gguf_file, **cached_file_kwargs)

    # We now download and resolve all checkpoint files if the checkpoint is sharded
    sharded_metadata = None
    if is_sharded:
        checkpoint_files, sharded_metadata = get_checkpoint_shard_files(
            pretrained_model_name_or_path,
            resolved_archive_file,
            cache_dir=cache_dir,
            force_download=force_download,
            proxies=proxies,
            local_files_only=local_files_only,
            token=token,
            user_agent=user_agent,
            revision=revision,
            subfolder=subfolder,
            _commit_hash=commit_hash,
            tqdm_class=tqdm_class,
        )
    else:
        checkpoint_files = [resolved_archive_file] if pretrained_model_name_or_path is not None else None

    return checkpoint_files, sharded_metadata