def has_file(
    path_or_repo: str | os.PathLike,
    filename: str,
    revision: str | None = None,
    proxies: dict[str, str] | None = None,
    token: bool | str | None = None,
    *,
    local_files_only: bool = False,
    cache_dir: str | Path | None = None,
    repo_type: str | None = None,
    **deprecated_kwargs,
):
    """
    Checks if a repo contains a given file without downloading it. Works for remote repos and local folders.

    If offline mode is enabled, checks if the file exists in the cache.

    <Tip warning={false}>

    This function will raise an error if the repository `path_or_repo` is not valid or if `revision` does not exist for
    this repo, but will return False for regular connection errors.

    </Tip>
    """
    # If path to local directory, check if the file exists
    if os.path.isdir(path_or_repo):
        return os.path.isfile(os.path.join(path_or_repo, filename))

    # Else it's a repo => let's check if the file exists in local cache or on the Hub

    # Check if file exists in cache
    # This information might be outdated so it's best to also make a HEAD call (if allowed).
    cached_path = try_to_load_from_cache(
        repo_id=path_or_repo,
        filename=filename,
        revision=revision,
        repo_type=repo_type,
        cache_dir=cache_dir,
    )
    has_file_in_cache = isinstance(cached_path, str)

    # If local_files_only, don't try the HEAD call
    if local_files_only:
        return has_file_in_cache

    # Check if the file exists
    try:
        response = get_session().head(
            hf_hub_url(path_or_repo, filename=filename, revision=revision, repo_type=repo_type),
            headers=build_hf_headers(token=token, user_agent=http_user_agent()),
            follow_redirects=False,
            timeout=10,
        )
    except httpx.ProxyError:
        # Actually raise for those subclasses of ConnectionError
        raise
    except (httpx.ConnectError, httpx.TimeoutException, OfflineModeIsEnabled):
        return has_file_in_cache

    try:
        hf_raise_for_status(response)
        return True
    except GatedRepoError as e:
        logger.error(e)
        raise OSError(
            f"{path_or_repo} is a gated repository. Make sure to request access at "
            f"https://huggingface.co/{path_or_repo} and pass a token having permission to this repo either by "
            "logging in with `hf auth login` or by passing `token=<your_token>`."
        ) from e
    except RepositoryNotFoundError as e:
        logger.error(e)
        raise OSError(f"{path_or_repo} is not a local folder or a valid repository name on 'https://hf.co'.") from e
    except RevisionNotFoundError as e:
        logger.error(e)
        raise OSError(
            f"{revision} is not a valid git identifier (branch name, tag name or commit id) that exists for this "
            f"model name. Check the model page at 'https://huggingface.co/{path_or_repo}' for available revisions."
        ) from e
    except EntryNotFoundError:
        return False  # File does not exist
    except HfHubHTTPError:
        # Any authentication/authorization error will be caught here => default to cache
        return has_file_in_cache