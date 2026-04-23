async def async_test_still(
    hass: HomeAssistant, info: Mapping[str, Any]
) -> tuple[dict[str, str], str | None]:
    """Verify that the still image is valid before we create an entity."""
    fmt = None
    if not (url := info.get(CONF_STILL_IMAGE_URL)):
        # If user didn't specify a still image URL,the automatically generated
        # still image that stream generates is always jpeg.
        return {}, info.get(CONF_CONTENT_TYPE, "image/jpeg")
    try:
        if not isinstance(url, template_helper.Template):
            url = template_helper.Template(url, hass)
        url = url.async_render(parse_result=False)
    except TemplateError as err:
        _LOGGER.warning("Problem rendering template %s: %s", url, err)
        return {CONF_STILL_IMAGE_URL: "template_error"}, None
    try:
        yarl_url = yarl.URL(url)
    except ValueError:
        return {CONF_STILL_IMAGE_URL: "malformed_url"}, None
    if not yarl_url.is_absolute():
        return {CONF_STILL_IMAGE_URL: "relative_url"}, None
    verify_ssl = info[SECTION_ADVANCED][CONF_VERIFY_SSL]
    auth = generate_auth(info)
    try:
        async_client = get_async_client(hass, verify_ssl=verify_ssl)
        async with asyncio.timeout(GET_IMAGE_TIMEOUT):
            response = await async_client.get(
                url, auth=auth, timeout=GET_IMAGE_TIMEOUT, follow_redirects=True
            )
            response.raise_for_status()
            image = response.content
    except (
        TimeoutError,
        RequestError,
        TimeoutException,
    ) as err:
        _LOGGER.error("Error getting camera image from %s: %s", url, type(err).__name__)
        return {CONF_STILL_IMAGE_URL: "unable_still_load"}, None
    except HTTPStatusError as err:
        _LOGGER.error(
            "Error getting camera image from %s: %s %s",
            url,
            type(err).__name__,
            err.response.text,
        )
        if err.response.status_code in [401, 403]:
            return {CONF_STILL_IMAGE_URL: "unable_still_load_auth"}, None
        if err.response.status_code == 404:
            return {CONF_STILL_IMAGE_URL: "unable_still_load_not_found"}, None
        if err.response.status_code in [500, 503]:
            return {CONF_STILL_IMAGE_URL: "unable_still_load_server_error"}, None
        return {CONF_STILL_IMAGE_URL: "unable_still_load"}, None

    if not image:
        return {CONF_STILL_IMAGE_URL: "unable_still_load_no_image"}, None
    fmt = get_image_type(image)
    _LOGGER.debug(
        "Still image at '%s' detected format: %s",
        info[CONF_STILL_IMAGE_URL],
        fmt,
    )
    if fmt not in SUPPORTED_IMAGE_TYPES:
        return {CONF_STILL_IMAGE_URL: "invalid_still_image"}, None
    return {}, f"image/{fmt}"