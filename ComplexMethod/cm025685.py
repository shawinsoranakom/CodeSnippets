def async_process_play_media_url(
    hass: HomeAssistant,
    media_content_id: str,
    *,
    allow_relative_url: bool = False,
    for_supervisor_network: bool = False,
) -> str:
    """Update a media URL with authentication if it points at Home Assistant."""
    parsed = yarl.URL(media_content_id)

    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return media_content_id

    if parsed.is_absolute():
        if not is_hass_url(hass, media_content_id):
            return media_content_id
    elif media_content_id[0] != "/":
        return media_content_id

    # https://github.com/pylint-dev/pylint/issues/3484
    # pylint: disable-next=using-constant-test
    if parsed.query:
        logging.getLogger(__name__).debug(
            "Not signing path for content with query param"
        )
    elif parsed.path.startswith(PATHS_WITHOUT_AUTH):
        # We don't sign this path if it doesn't need auth. Although signing itself can't
        # hurt, some devices are unable to handle long URLs and the auth signature might
        # push it over.
        pass
    else:
        signed_path = async_sign_path(
            hass,
            quote(parsed.path),
            timedelta(seconds=CONTENT_AUTH_EXPIRY_TIME),
        )
        media_content_id = str(parsed.join(yarl.URL(signed_path)))

    # convert relative URL to absolute URL
    if not parsed.is_absolute() and not allow_relative_url:
        base_url = None
        if for_supervisor_network:
            base_url = get_supervisor_network_url(hass)

        if not base_url:
            try:
                base_url = get_url(hass)
            except NoURLAvailableError as err:
                msg = "Unable to determine Home Assistant URL to send to device"
                if (
                    hass.config.api
                    and hass.config.api.use_ssl
                    and (not hass.config.external_url or not hass.config.internal_url)
                ):
                    msg += ". Configure internal and external URL in general settings."
                raise HomeAssistantError(msg) from err

        media_content_id = f"{base_url}{media_content_id}"

    return media_content_id