async def async_test_and_preview_stream(
    hass: HomeAssistant, info: Mapping[str, Any]
) -> Stream | None:
    """Verify that the stream is valid before we create an entity.

    Returns the stream object if valid. Raises InvalidStreamException if not.
    The stream object is used to preview the video in the UI.
    """
    if not (stream_source := info.get(CONF_STREAM_SOURCE)):
        return None

    if not isinstance(stream_source, template_helper.Template):
        stream_source = template_helper.Template(stream_source, hass)
    try:
        stream_source = stream_source.async_render(parse_result=False)
    except TemplateError as err:
        _LOGGER.warning("Problem rendering template %s: %s", stream_source, err)
        raise InvalidStreamException("template_error") from err
    stream_options: dict[str, str | bool | float] = {}
    if rtsp_transport := info[SECTION_ADVANCED].get(CONF_RTSP_TRANSPORT):
        stream_options[CONF_RTSP_TRANSPORT] = rtsp_transport
    if info[SECTION_ADVANCED].get(CONF_USE_WALLCLOCK_AS_TIMESTAMPS):
        stream_options[CONF_USE_WALLCLOCK_AS_TIMESTAMPS] = True

    try:
        url = yarl.URL(stream_source)
    except ValueError as err:
        raise InvalidStreamException("malformed_url") from err
    if not url.is_absolute():
        raise InvalidStreamException("relative_url")
    if not url.user and not url.password:
        username = info.get(CONF_USERNAME)
        password = info.get(CONF_PASSWORD)
        if username and password:
            url = url.with_user(username).with_password(password)
            stream_source = str(url)
    try:
        stream = create_stream(
            hass,
            stream_source,
            stream_options,
            DynamicStreamSettings(),
            f"{DOMAIN}.test_stream",
        )
        hls_provider = stream.add_provider(HLS_PROVIDER)
    except PermissionError as err:
        raise InvalidStreamException("stream_not_permitted") from err
    except OSError as err:
        if err.errno == EHOSTUNREACH:
            raise InvalidStreamException("stream_no_route_to_host") from err
        if err.errno == EIO:  # input/output error
            raise InvalidStreamException("stream_io_error") from err
        raise
    except HomeAssistantError as err:
        if "Stream integration is not set up" in str(err):
            raise InvalidStreamException("stream_not_set_up") from err
        raise
    await stream.start()
    if not await hls_provider.part_recv(timeout=SOURCE_TIMEOUT):
        hass.async_create_task(stream.stop())
        raise InvalidStreamException("timeout")
    return stream