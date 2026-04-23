def _convert_stream_options(
    hass: HomeAssistant,
    stream_source: str,
    stream_options: Mapping[str, str | bool | float],
) -> tuple[dict[str, str], StreamSettings]:
    """Convert options from stream options into PyAV options and stream settings."""
    if DOMAIN not in hass.data:
        raise HomeAssistantError("Stream integration is not set up.")

    stream_settings = copy.copy(hass.data[DOMAIN][ATTR_SETTINGS])
    pyav_options: dict[str, str] = {}
    try:
        STREAM_OPTIONS_SCHEMA(stream_options)
    except vol.Invalid as exc:
        raise HomeAssistantError(f"Invalid stream options: {exc}") from exc

    if extra_wait_time := stream_options.get(CONF_EXTRA_PART_WAIT_TIME):
        stream_settings.hls_part_timeout += extra_wait_time
    if rtsp_transport := stream_options.get(CONF_RTSP_TRANSPORT):
        assert isinstance(rtsp_transport, str)
        # The PyAV options currently match the stream CONF constants, but this
        # will not necessarily always be the case, so they are hard coded here
        pyav_options["rtsp_transport"] = rtsp_transport
    if stream_options.get(CONF_USE_WALLCLOCK_AS_TIMESTAMPS):
        pyav_options["use_wallclock_as_timestamps"] = "1"

    # For RTSP streams, prefer TCP
    if isinstance(stream_source, str) and stream_source[:7] == "rtsp://":
        pyav_options = {
            "rtsp_flags": ATTR_PREFER_TCP,
            "stimeout": "5000000",
            **pyav_options,
        }
    return pyav_options, stream_settings