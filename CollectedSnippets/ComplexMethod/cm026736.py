def websocket_update_entity(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Handle update entity websocket command.

    Async friendly.
    """
    registry = er.async_get(hass)

    entity_id = msg["entity_id"]
    if not (entity_entry := registry.async_get(entity_id)):
        connection.send_message(
            websocket_api.error_message(msg["id"], ERR_NOT_FOUND, "Entity not found")
        )
        return

    changes: dict[str, Any] = {}

    for key in (
        "area_id",
        "device_class",
        "disabled_by",
        "hidden_by",
        "icon",
        "name",
        "new_entity_id",
    ):
        if key in msg:
            changes[key] = msg[key]

    if "aliases" in msg:
        # Sanitize aliases by removing:
        #   - Trailing and leading whitespace characters in the individual aliases
        #   - Empty strings
        changes["aliases"] = aliases = []
        for alias in msg["aliases"]:
            if alias is None:
                aliases.append(er.COMPUTED_NAME)
            elif alias := alias.strip():
                aliases.append(alias)

    if "labels" in msg:
        # Convert labels to a set
        changes["labels"] = set(msg["labels"])

    if "disabled_by" in msg and msg["disabled_by"] is None:
        # Don't allow enabling an entity of a disabled device
        if entity_entry.device_id:
            device_registry = dr.async_get(hass)
            device = device_registry.async_get(entity_entry.device_id)
            if device and device.disabled:
                connection.send_message(
                    websocket_api.error_message(
                        msg["id"], "invalid_info", "Device is disabled"
                    )
                )
                return

    # Update the categories if provided
    if "categories" in msg:
        categories = entity_entry.categories.copy()
        for scope, category_id in msg["categories"].items():
            if scope in categories and category_id is None:
                # Remove the category from the scope as it was unset
                del categories[scope]
            elif category_id is not None:
                # Add or update the category for the given scope
                categories[scope] = category_id
        changes["categories"] = categories

    try:
        if changes:
            entity_entry = registry.async_update_entity(entity_id, **changes)
    except ValueError as err:
        connection.send_message(
            websocket_api.error_message(msg["id"], "invalid_info", str(err))
        )
        return

    if "new_entity_id" in msg:
        entity_id = msg["new_entity_id"]

    try:
        if "options_domain" in msg:
            entity_entry = registry.async_update_entity_options(
                entity_id, msg["options_domain"], msg["options"]
            )
    except ValueError as err:
        connection.send_message(
            websocket_api.error_message(msg["id"], "invalid_info", str(err))
        )
        return

    result: dict[str, Any] = {"entity_entry": entity_entry.extended_dict}
    if "disabled_by" in changes and changes["disabled_by"] is None:
        # Enabling an entity requires a config entry reload, or HA restart
        if not (config_entry_id := entity_entry.config_entry_id) or (
            (config_entry := hass.config_entries.async_get_entry(config_entry_id))
            and not config_entry.supports_unload
        ):
            result["require_restart"] = True
        else:
            result["reload_delay"] = config_entries.RELOAD_AFTER_UPDATE_DELAY
    connection.send_result(msg["id"], result)