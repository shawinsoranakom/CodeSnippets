async def load_data(
    hass: HomeAssistant,
    url: str | None,
    filepath: str | None,
    username: str,
    password: str,
    authentication: str | None,
    verify_ssl: bool,
    num_retries: int = 5,
) -> io.BytesIO:
    """Load data into ByteIO/File container from a source."""
    if url is not None:
        # Load data from URL
        params: dict[str, Any] = {}
        headers: dict[str, str] = {}
        _validate_credentials_input(authentication, username, password)
        if authentication == HTTP_BEARER_AUTHENTICATION:
            headers = {"Authorization": f"Bearer {password}"}
        elif authentication == HTTP_DIGEST_AUTHENTICATION:
            params["auth"] = httpx.DigestAuth(username, password)
        elif authentication == HTTP_BASIC_AUTHENTICATION:
            params["auth"] = httpx.BasicAuth(username, password)

        retry_num = 0
        async with get_async_client(hass, verify_ssl) as client:
            while retry_num < num_retries:
                try:
                    response = await client.get(
                        url, headers=headers, timeout=DEFAULT_TIMEOUT_SECONDS, **params
                    )
                except (httpx.HTTPError, httpx.InvalidURL) as err:
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="failed_to_load_url",
                        translation_placeholders={"error": str(err)},
                    ) from err

                if response.status_code != 200:
                    _LOGGER.warning(
                        "Status code %s (retry #%s) loading %s",
                        response.status_code,
                        retry_num + 1,
                        url,
                    )
                else:
                    data = io.BytesIO(response.content)
                    if data.read():
                        data.seek(0)
                        data.name = url
                        _LOGGER.debug("file downloaded: %s", url)
                        return data
                    _LOGGER.warning("Empty data (retry #%s) in %s)", retry_num + 1, url)
                retry_num += 1
                if retry_num < num_retries:
                    await asyncio.sleep(
                        1
                    )  # Add a sleep to allow other async operations to proceed
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="failed_to_load_url",
                translation_placeholders={"error": str(response.status_code)},
            )
    elif filepath is not None:
        if hass.config.is_allowed_path(filepath):
            return await hass.async_add_executor_job(_read_file_as_bytesio, filepath)

        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="allowlist_external_dirs_error",
        )
    else:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="missing_input",
            translation_placeholders={"field": "URL or File"},
        )