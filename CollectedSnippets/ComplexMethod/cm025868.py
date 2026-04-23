async def _async_get_requests(call: ServiceCall) -> ServiceResponse:
    """Get requests made to Overseerr."""
    entry: OverseerrConfigEntry = service.async_get_config_entry(
        call.hass, DOMAIN, call.data[ATTR_CONFIG_ENTRY_ID]
    )
    client = entry.runtime_data.client
    kwargs: dict[str, Any] = {}
    if status := call.data.get(ATTR_STATUS):
        kwargs["status"] = status
    if sort_order := call.data.get(ATTR_SORT_ORDER):
        kwargs["sort"] = sort_order
    if requested_by := call.data.get(ATTR_REQUESTED_BY):
        kwargs["requested_by"] = requested_by
    try:
        requests = await client.get_requests(**kwargs)
    except OverseerrConnectionError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="connection_error",
            translation_placeholders={"error": str(err)},
        ) from err
    result: list[dict[str, Any]] = []
    for request in requests:
        req = asdict(request)
        assert request.media.tmdb_id
        req["media"] = await _get_media(
            client, request.media.media_type, request.media.tmdb_id
        )
        for user in (req["modified_by"], req["requested_by"]):
            del user["avatar_e_tag"]
            del user["avatar_version"]
            del user["permissions"]
            del user["recovery_link_expiration_date"]
            del user["settings"]
            del user["user_type"]
            del user["warnings"]
        result.append(req)

    return {"requests": cast(list[JsonValueType], result)}