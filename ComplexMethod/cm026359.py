async def download_pr_artifact(
    hass: HomeAssistant,
    pr_number: int,
    github_token: str,
    tmp_dir: pathlib.Path,
) -> pathlib.Path:
    """Download and extract frontend PR artifact from GitHub.

    Returns the path to the tmp directory containing hass_frontend/.
    Raises HomeAssistantError on failure.
    """
    try:
        session = async_get_clientsession(hass)
    except Exception as err:
        raise HomeAssistantError(f"Failed to get HTTP client session: {err}") from err

    client = GitHubAPI(token=github_token, session=session)

    head_sha, base_sha = await _get_pr_shas(client, pr_number)
    cache_key = f"{head_sha}:{base_sha}"

    frontend_dir = tmp_dir / "hass_frontend"
    sha_file = tmp_dir / ".sha"

    if frontend_dir.exists() and sha_file.exists():
        try:
            cached_key = await hass.async_add_executor_job(sha_file.read_text)
            cached_key = cached_key.strip()
            if cached_key == cache_key:
                _LOGGER.info(
                    "Using cached PR #%s (commit %s) from %s",
                    pr_number,
                    cache_key,
                    tmp_dir,
                )
                return tmp_dir
            _LOGGER.info(
                "PR #%s cache outdated (cached: %s, current: %s), re-downloading",
                pr_number,
                cached_key,
                cache_key,
            )
        except OSError as err:
            _LOGGER.debug("Failed to read cache SHA file: %s", err)

    artifact_url = await _find_pr_artifact(client, pr_number, head_sha)

    _LOGGER.info("Downloading frontend PR #%s artifact", pr_number)
    artifact_data = await _download_artifact_data(hass, artifact_url, github_token)

    try:
        await hass.async_add_executor_job(
            _extract_artifact, artifact_data, tmp_dir, cache_key
        )
    except zipfile.BadZipFile as err:
        raise HomeAssistantError(
            f"Downloaded artifact for PR #{pr_number} is corrupted or invalid"
        ) from err
    except ValueError as err:
        raise HomeAssistantError(
            f"Downloaded artifact for PR #{pr_number} failed validation: {err}"
        ) from err
    except OSError as err:
        raise HomeAssistantError(
            f"Failed to extract artifact for PR #{pr_number}: {err}"
        ) from err

    _LOGGER.info(
        "Successfully downloaded and extracted PR #%s (commit %s) to %s",
        pr_number,
        head_sha[:8],
        tmp_dir,
    )
    return tmp_dir