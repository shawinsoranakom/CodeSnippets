def _get_cached_action_parameters(
    hass: HomeAssistant, domain: str, action: str
) -> tuple[str | None, vol.Schema]:
    """Get action description and schema."""
    description = None
    parameters = vol.Schema({})

    parameters_cache = hass.data.get(ACTION_PARAMETERS_CACHE)

    if parameters_cache is None:
        parameters_cache = hass.data[ACTION_PARAMETERS_CACHE] = {}

        @callback
        def clear_cache(event: Event) -> None:
            """Clear action parameter cache on action removal."""
            if (
                event.data[ATTR_DOMAIN] in parameters_cache
                and event.data[ATTR_SERVICE]
                in parameters_cache[event.data[ATTR_DOMAIN]]
            ):
                parameters_cache[event.data[ATTR_DOMAIN]].pop(event.data[ATTR_SERVICE])

        cancel = hass.bus.async_listen(EVENT_SERVICE_REMOVED, clear_cache)

        @callback
        def on_homeassistant_close(event: Event) -> None:
            """Cleanup."""
            cancel()

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_CLOSE, on_homeassistant_close)

    if domain in parameters_cache and action in parameters_cache[domain]:
        return parameters_cache[domain][action]

    if action_desc := service.async_get_cached_service_description(
        hass, domain, action
    ):
        description = action_desc.get("description")
        schema: dict[vol.Marker, Any] = {}
        fields = action_desc.get("fields", {})

        for field, config in fields.items():
            field_description = config.get("description")
            if not field_description:
                field_description = config.get("name")
            key: vol.Marker
            if config.get("required"):
                key = vol.Required(field, description=field_description)
            else:
                key = vol.Optional(field, description=field_description)
            if "selector" in config:
                schema[key] = selector.selector(config["selector"])
            else:
                schema[key] = cv.string

        parameters = vol.Schema(schema)

        if domain == SCRIPT_DOMAIN:
            entity_registry = er.async_get(hass)
            if (
                entity_id := entity_registry.async_get_entity_id(domain, domain, action)
            ) is not None and (
                entity_entry := entity_registry.async_get(entity_id)
            ) is not None:
                aliases = er.async_get_entity_aliases(hass, entity_entry)
                if aliases:
                    if description:
                        description = description + ". Aliases: " + str(list(aliases))
                    else:
                        description = "Aliases: " + str(list(aliases))

        parameters_cache.setdefault(domain, {})[action] = (description, parameters)

    return description, parameters