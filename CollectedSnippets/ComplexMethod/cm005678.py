def cached_files(
    path_or_repo_id: str | os.PathLike,
    filenames: list[str],
    cache_dir: str | os.PathLike | None = None,
    force_download: bool = False,
    proxies: dict[str, str] | None = None,
    token: bool | str | None = None,
    revision: str | None = None,
    local_files_only: bool = False,
    subfolder: str = "",
    repo_type: str | None = None,
    user_agent: str | dict[str, str] | None = None,
    _raise_exceptions_for_gated_repo: bool = True,
    _raise_exceptions_for_missing_entries: bool = True,
    _raise_exceptions_for_connection_errors: bool = True,
    _commit_hash: str | None = None,
    tqdm_class: type | None = None,
    **deprecated_kwargs,
) -> list[str] | None:
    """
    Tries to locate several files in a local folder and repo, downloads and cache them if necessary.

    Args:
        path_or_repo_id (`str` or `os.PathLike`):
            This can be either:
            - a string, the *model id* of a model repo on huggingface.co.
            - a path to a *directory* potentially containing the file.
        filenames (`list[str]`):
            The name of all the files to locate in `path_or_repo`.
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
            If `True`, will only try to load the tokenizer configuration from local files.
        subfolder (`str`, *optional*, defaults to `""`):
            In case the relevant files are located inside a subfolder of the model repo on huggingface.co, you can
            specify the folder name here.
        repo_type (`str`, *optional*):
            Specify the repo type (useful when downloading from a space for instance).

    Private args:
        _raise_exceptions_for_gated_repo (`bool`):
            if False, do not raise an exception for gated repo error but return None.
        _raise_exceptions_for_missing_entries (`bool`):
            if False, do not raise an exception for missing entries but return None.
        _raise_exceptions_for_connection_errors (`bool`):
            if False, do not raise an exception for connection errors but return None.
        _commit_hash (`str`, *optional*):
            passed when we are chaining several calls to various files (e.g. when loading a tokenizer or
            a pipeline). If files are cached for this commit hash, avoid calls to head and get from the cache.

    <Tip>

    Passing `token=True` is required when you want to use a private model.

    </Tip>

    Returns:
        `Optional[str]`: Returns the resolved file (to the cache folder if downloaded from a repo).

    Examples:

    ```python
    # Download a model weight from the Hub and cache it.
    model_weights_file = cached_file("google-bert/bert-base-uncased", "pytorch_model.bin")
    ```
    """
    if is_offline_mode() and not local_files_only:
        logger.info("Offline mode: forcing local_files_only=True")
        local_files_only = True
    if subfolder is None:
        subfolder = ""

    # Add folder to filenames
    full_filenames = [os.path.join(subfolder, file) for file in filenames]

    path_or_repo_id = str(path_or_repo_id)
    existing_files = []
    for filename in full_filenames:
        if os.path.isdir(path_or_repo_id):
            resolved_file = os.path.join(path_or_repo_id, filename)
            if not os.path.isfile(resolved_file):
                if _raise_exceptions_for_missing_entries and filename != os.path.join(subfolder, "config.json"):
                    revision_ = "main" if revision is None else revision
                    raise OSError(
                        f"{path_or_repo_id} does not appear to have a file named {filename}. Checkout "
                        f"'https://huggingface.co/{path_or_repo_id}/tree/{revision_}' for available files."
                    )
                else:
                    continue
            existing_files.append(resolved_file)

    if os.path.isdir(path_or_repo_id):
        return existing_files if existing_files else None

    if cache_dir is None:
        cache_dir = constants.HF_HUB_CACHE
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)

    existing_files = []
    file_counter = 0
    if _commit_hash is not None and not force_download:
        for filename in full_filenames:
            # If the file is cached under that commit hash, we return it directly.
            resolved_file = try_to_load_from_cache(
                path_or_repo_id, filename, cache_dir=cache_dir, revision=_commit_hash, repo_type=repo_type
            )
            if resolved_file is not None:
                if resolved_file is not _CACHED_NO_EXIST:
                    file_counter += 1
                    existing_files.append(resolved_file)
                elif not _raise_exceptions_for_missing_entries:
                    file_counter += 1
                else:
                    raise OSError(f"Could not locate {filename} inside {path_or_repo_id}.")

    # Either all the files were found, or some were _CACHED_NO_EXIST but we do not raise for missing entries
    if file_counter == len(full_filenames):
        return existing_files if len(existing_files) > 0 else None

    user_agent = http_user_agent(user_agent)
    # download the files if needed
    try:
        if len(full_filenames) == 1:
            # This is slightly better for only 1 file
            hf_hub_download(
                path_or_repo_id,
                filenames[0],
                subfolder=None if len(subfolder) == 0 else subfolder,
                repo_type=repo_type,
                revision=revision,
                cache_dir=cache_dir,
                user_agent=user_agent,
                force_download=force_download,
                proxies=proxies,
                token=token,
                local_files_only=local_files_only,
                tqdm_class=tqdm_class,
            )
        else:
            snapshot_download(
                path_or_repo_id,
                allow_patterns=full_filenames,
                repo_type=repo_type,
                revision=revision,
                cache_dir=cache_dir,
                user_agent=user_agent,
                force_download=force_download,
                proxies=proxies,
                token=token,
                local_files_only=local_files_only,
                tqdm_class=tqdm_class,
            )

    except Exception as e:
        # We cannot recover from them
        if isinstance(e, RepositoryNotFoundError) and not isinstance(e, GatedRepoError):
            raise OSError(
                f"{path_or_repo_id} is not a local folder and is not a valid model identifier "
                "listed on 'https://huggingface.co/models'\nIf this is a private repository, make sure to pass a token "
                "having permission to this repo either by logging in with `hf auth login` or by passing "
                "`token=<your_token>`"
            ) from e
        elif isinstance(e, RevisionNotFoundError):
            raise OSError(
                f"{revision} is not a valid git identifier (branch name, tag name or commit id) that exists "
                "for this model name. Check the model page at "
                f"'https://huggingface.co/{path_or_repo_id}' for available revisions."
            ) from e
        elif isinstance(e, PermissionError):
            raise OSError(
                f"PermissionError at {e.filename} when downloading {path_or_repo_id}. "
                "Check cache directory permissions. Common causes: 1) another user is downloading the same model (please wait); "
                "2) a previous download was canceled and the lock file needs manual removal."
            ) from e
        elif isinstance(e, ValueError):
            raise OSError(f"{e}") from e

        # Now we try to recover if we can find all files correctly in the cache
        resolved_files = [
            _get_cache_file_to_return(path_or_repo_id, filename, cache_dir, revision, repo_type)
            for filename in full_filenames
        ]
        if all(file is not None for file in resolved_files):
            return resolved_files

        # Raise based on the flags. Note that we will raise for missing entries at the very end, even when
        # not entering this Except block, as it may also happen when `snapshot_download` does not raise
        if isinstance(e, GatedRepoError):
            if not _raise_exceptions_for_gated_repo:
                return None
            raise OSError(
                "You are trying to access a gated repo.\nMake sure to have access to it at "
                f"https://huggingface.co/{path_or_repo_id}.\n{str(e)}"
            ) from e
        elif isinstance(e, LocalEntryNotFoundError):
            if not _raise_exceptions_for_connection_errors:
                return None
            # Here we only raise if both flags for missing entry and connection errors are True (because it can be raised
            # even when `local_files_only` is True, in which case raising for connections errors only would not make sense)
            elif _raise_exceptions_for_missing_entries:
                raise OSError(
                    f"We couldn't connect to '{constants.ENDPOINT}' to load the files, and couldn't find them in the"
                    f" cached files.\nCheck your internet connection or see how to run the library in offline mode at"
                    " 'https://huggingface.co/docs/transformers/installation#offline-mode'."
                ) from e
        # snapshot_download will not raise EntryNotFoundError, but hf_hub_download can. If this is the case, it will be treated
        # later on anyway and re-raised if needed
        elif isinstance(e, HfHubHTTPError) and not isinstance(e, EntryNotFoundError):
            if not _raise_exceptions_for_connection_errors:
                return None
            raise OSError(f"There was a specific connection error when trying to load {path_or_repo_id}:\n{e}") from e
        # Any other Exception type should now be re-raised, in order to provide helpful error messages and break the execution flow
        # (EntryNotFoundError will be treated outside this block and correctly re-raised if needed)
        elif not isinstance(e, EntryNotFoundError):
            raise e

    resolved_files = [
        _get_cache_file_to_return(path_or_repo_id, filename, cache_dir, revision) for filename in full_filenames
    ]
    # If there are any missing file and the flag is active, raise
    if any(file is None for file in resolved_files) and _raise_exceptions_for_missing_entries:
        missing_entries = [original for original, resolved in zip(full_filenames, resolved_files) if resolved is None]
        # Last escape
        if len(resolved_files) == 1 and missing_entries[0] == os.path.join(subfolder, "config.json"):
            return None
        # Now we raise for missing entries
        revision_ = "main" if revision is None else revision
        msg = (
            f"a file named {missing_entries[0]}" if len(missing_entries) == 1 else f"files named {(*missing_entries,)}"
        )
        raise OSError(
            f"{path_or_repo_id} does not appear to have {msg}. Checkout 'https://huggingface.co/{path_or_repo_id}/tree/{revision_}'"
            " for available files."
        )

    # Remove potential missing entries (we can silently remove them at this point based on the flags)
    resolved_files = [file for file in resolved_files if file is not None]
    # Return `None` if the list is empty, coherent with other Exception when the flag is not active
    resolved_files = None if len(resolved_files) == 0 else resolved_files

    return resolved_files