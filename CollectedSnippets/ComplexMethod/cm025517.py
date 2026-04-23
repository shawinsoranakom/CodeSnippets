def process_plex_payload(
    hass: HomeAssistant,
    content_type: str,
    content_id: str,
    default_plex_server: PlexServer | None = None,
    supports_playqueues: bool = True,
) -> PlexMediaSearchResult:
    """Look up Plex media using media_player.play_media service payloads."""
    plex_server = default_plex_server
    extra_params = {}

    if content_id.startswith(PLEX_URI_SCHEME + "{"):
        # Handle the special payload of 'plex://{<json>}'
        content_id = content_id.removeprefix(PLEX_URI_SCHEME)
        content = json.loads(content_id)
    elif content_id.startswith(PLEX_URI_SCHEME):
        # Handle standard media_browser payloads
        plex_url = URL(content_id)
        # https://github.com/pylint-dev/pylint/issues/3484
        # pylint: disable-next=using-constant-test
        if plex_url.name:
            if len(plex_url.parts) == 2:
                if plex_url.name == "search":
                    content = {}
                else:
                    content = int(plex_url.name)
            else:
                # For "special" items like radio stations
                content = plex_url.path
            server_id = plex_url.host
            plex_server = get_plex_server(hass, plex_server_id=server_id)
        else:  # noqa: PLR5501
            # Handle legacy payloads without server_id in URL host position
            if plex_url.host == "search":
                content = {}
            else:
                content = int(plex_url.host)  # type: ignore[arg-type]
        extra_params = dict(plex_url.query)
    else:
        content = json.loads(content_id)

    if isinstance(content, dict):
        if plex_server_name := content.pop("plex_server", None):
            plex_server = get_plex_server(hass, plex_server_name)

    if not plex_server:
        plex_server = get_plex_server(hass)

    if isinstance(content, dict):
        if plex_user := content.pop("username", None):
            _LOGGER.debug("Switching to Plex user: %s", plex_user)
            plex_server = plex_server.switch_user(plex_user)

    if content_type == "station":
        if not supports_playqueues:
            raise HomeAssistantError("Plex stations are not supported on this device")
        playqueue = plex_server.create_station_playqueue(content)
        return PlexMediaSearchResult(playqueue)

    if isinstance(content, int):
        content = {"plex_key": content}
        content_type = DOMAIN

    content.update(extra_params)

    if playqueue_id := content.pop("playqueue_id", None):
        if not supports_playqueues:
            raise HomeAssistantError("Plex playqueues are not supported on this device")
        try:
            playqueue = plex_server.get_playqueue(playqueue_id)
        except NotFound as err:
            raise MediaNotFound(
                f"PlayQueue '{playqueue_id}' could not be found"
            ) from err
        return PlexMediaSearchResult(playqueue, content)

    search_query = content.copy()
    shuffle = search_query.pop("shuffle", 0)
    continuous = search_query.pop("continuous", 0)

    # Remove internal kwargs before passing copy to plexapi
    for internal_key in ("resume", "offset"):
        search_query.pop(internal_key, None)

    media = plex_server.lookup_media(content_type, **search_query)

    if supports_playqueues and (isinstance(media, list) or shuffle or continuous):
        playqueue = plex_server.create_playqueue(
            media,
            includeRelated=0,
            shuffle=1 if shuffle else 0,
            continuous=1 if continuous else 0,
        )
        return PlexMediaSearchResult(playqueue, content)

    return PlexMediaSearchResult(media, content)