async def async_setup_entry(hass: HomeAssistant, entry: OllamaConfigEntry) -> bool:
    """Set up Ollama from a config entry."""
    settings = {**entry.data, **entry.options}
    api_key = settings.get(CONF_API_KEY)
    stripped_api_key = api_key.strip() if isinstance(api_key, str) else None
    client = ollama.AsyncClient(
        host=settings[CONF_URL],
        headers=(
            {"Authorization": f"Bearer {stripped_api_key}"}
            if stripped_api_key
            else None
        ),
        verify=get_default_context(),
    )
    try:
        async with asyncio.timeout(DEFAULT_TIMEOUT):
            await client.list()
    except ollama.ResponseError as err:
        if err.status_code in (401, 403):
            raise ConfigEntryAuthFailed from err
        if err.status_code >= 500 or err.status_code == 429:
            raise ConfigEntryNotReady(err) from err
        # If the response is a 4xx error other than 401 or 403, it likely means the URL is valid but not an Ollama instance,
        # so we raise ConfigEntryError to show an error in the UI, instead of ConfigEntryNotReady which would just keep retrying.
        raise ConfigEntryError(err) from err
    except (TimeoutError, httpx.ConnectError) as err:
        raise ConfigEntryNotReady(err) from err

    entry.runtime_data = client
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True