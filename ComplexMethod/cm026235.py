def _warn_chat_id_migration(service: ServiceCall) -> set[int]:
    if not service.data.get(ATTR_TARGET):
        return set()

    chat_ids: set[int] = set(
        [service.data[ATTR_TARGET]]
        if isinstance(service.data[ATTR_TARGET], int)
        else service.data[ATTR_TARGET]
    )

    # default: service was called using frontend such as developer tools or automation editor
    service_call_origin = "call_service"

    origin = service.context.origin_event
    if origin and ATTR_ENTITY_ID in origin.data:
        # automation
        service_call_origin = origin.data[ATTR_ENTITY_ID]
    elif origin and origin.data.get(ATTR_DOMAIN) == SCRIPT_DOMAIN:
        # script
        service_call_origin = f"{origin.data[ATTR_DOMAIN]}.{origin.data[ATTR_SERVICE]}"

    ir.async_create_issue(
        service.hass,
        DOMAIN,
        f"migrate_chat_ids_in_target_{service_call_origin}_{service.service}",
        breaks_in_ha_version="2026.9.0",
        is_fixable=True,
        is_persistent=True,
        severity=ir.IssueSeverity.WARNING,
        translation_key="migrate_chat_ids_in_target",
        translation_placeholders={
            "integration_title": "Telegram Bot",
            "action": f"{DOMAIN}.{service.service}",
            "chat_ids": ", ".join(str(chat_id) for chat_id in chat_ids),
            "action_origin": service_call_origin,
            "telegram_bot_entities_url": "/config/entities?domain=telegram_bot",
            "example_old": f"```yaml\naction: {service.service}\ndata:\n  target:  # to be updated\n    - 1234567890\n...\n```",
            "example_new_entity_id": f"```yaml\naction: {service.service}\ndata:\n  entity_id:\n    - notify.telegram_bot_1234567890_1234567890  # replace with your notify entity\n...\n```",
            "example_new_chat_id": f"```yaml\naction: {service.service}\ndata:\n  chat_id:\n    - 1234567890  # replace with your chat_id\n...\n```",
        },
        learn_more_url="https://github.com/home-assistant/core/pull/154868",
    )

    return chat_ids