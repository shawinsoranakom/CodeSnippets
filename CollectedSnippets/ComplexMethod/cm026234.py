def _build_targets(
    service: ServiceCall,
) -> list[tuple[TelegramBotConfigEntry, int, str]]:
    """Builds a list of targets from the service parameters.

    Each target is a tuple of (config_entry, chat_id, notify_entity_id).
    The config_entry identifies the bot to use for the service call.
    The chat_id or notify_entity_id identifies the recipient of the message.
    """

    migrate_chat_ids = _warn_chat_id_migration(service)

    targets: list[tuple[TelegramBotConfigEntry, int, str]] = []

    # build target list from notify entities using service data: `entity_id`

    referenced = async_extract_referenced_entity_ids(
        service.hass, TargetSelection(service.data)
    )
    notify_entity_ids = referenced.referenced | referenced.indirectly_referenced

    # parse entity IDs
    entity_registry = er.async_get(service.hass)
    for notify_entity_id in notify_entity_ids:
        # get config entry from notify entity
        entity_entry = entity_registry.async_get(notify_entity_id)
        if not entity_entry:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_notify_entity",
                translation_placeholders={ATTR_ENTITY_ID: notify_entity_id},
            )
        assert entity_entry.config_entry_id is not None
        notify_config_entry = service.hass.config_entries.async_get_known_entry(
            entity_entry.config_entry_id
        )

        # get chat id from subentry
        assert entity_entry.config_subentry_id is not None
        notify_config_subentry = notify_config_entry.subentries[
            entity_entry.config_subentry_id
        ]
        notify_chat_id: int = notify_config_subentry.data[ATTR_CHAT_ID]

        targets.append((notify_config_entry, notify_chat_id, notify_entity_id))

    # build target list using service data: `config_entry_id` and `chat_id`

    config_entry: TelegramBotConfigEntry | None = None
    if CONF_CONFIG_ENTRY_ID in service.data:
        # parse config entry from service data
        config_entry_id: str = service.data[CONF_CONFIG_ENTRY_ID]
        config_entry = service.hass.config_entries.async_get_known_entry(
            config_entry_id
        )
    else:
        # config entry not provided so we try to determine the default
        config_entries: list[TelegramBotConfigEntry] = (
            service.hass.config_entries.async_entries(DOMAIN)
        )
        if len(config_entries) == 1:
            config_entry = config_entries[0]

    # parse chat IDs from service data: `chat_id`
    if config_entry is not None:
        chat_ids: set[int] = migrate_chat_ids
        if ATTR_CHAT_ID in service.data:
            chat_ids = chat_ids | set(
                [service.data[ATTR_CHAT_ID]]
                if isinstance(service.data[ATTR_CHAT_ID], int)
                else service.data[ATTR_CHAT_ID]
            )

        if not chat_ids and not targets:
            # no targets from service data, so we default to the first allowed chat IDs of the config entry
            subentries = list(config_entry.subentries.values())
            if not subentries:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="missing_allowed_chat_ids",
                    translation_placeholders={
                        "bot_name": config_entry.title,
                    },
                )

            default_chat_id: int = subentries[0].data[ATTR_CHAT_ID]
            _LOGGER.debug(
                "Defaulting to chat ID %s for bot %s",
                default_chat_id,
                config_entry.title,
            )
            chat_ids = {default_chat_id}

        invalid_chat_ids: set[int] = set()
        for chat_id in chat_ids:
            # map chat_id to notify entity ID

            if config_entry.state is not ConfigEntryState.LOADED:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="entry_not_loaded",
                    translation_placeholders={"telegram_bot": config_entry.title},
                )

            entity_id = entity_registry.async_get_entity_id(
                "notify",
                DOMAIN,
                f"{config_entry.runtime_data.bot.id}_{chat_id}",
            )

            if not entity_id:
                invalid_chat_ids.add(chat_id)
            else:
                targets.append((config_entry, chat_id, entity_id))

        if invalid_chat_ids:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_chat_ids",
                translation_placeholders={
                    "chat_ids": ", ".join(str(chat_id) for chat_id in invalid_chat_ids),
                    "bot_name": config_entry.title,
                },
            )

    # we're done building targets from service data
    if targets:
        return targets

    # can't determine default since multiple config entries exist
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="missing_notify_entities",
    )