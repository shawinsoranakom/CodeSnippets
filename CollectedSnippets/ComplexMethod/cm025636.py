async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: GoogleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the google calendar platform."""
    calendar_service = config_entry.runtime_data.service
    store = config_entry.runtime_data.store
    try:
        result = await calendar_service.async_list_calendars()
    except ApiException as err:
        raise PlatformNotReady(str(err)) from err

    entity_registry = er.async_get(hass)
    registry_entries = er.async_entries_for_config_entry(
        entity_registry, config_entry.entry_id
    )
    entity_entry_map = {
        entity_entry.unique_id: entity_entry for entity_entry in registry_entries
    }

    # Yaml configuration may override objects from the API
    calendars = await hass.async_add_executor_job(
        load_config, hass.config.path(YAML_DEVICES)
    )
    new_calendars = []
    entities = []
    for calendar_item in result.items:
        calendar_id = calendar_item.id
        if calendars and calendar_id in calendars:
            calendar_info = calendars[calendar_id]
        else:
            calendar_info = get_calendar_info(
                hass, calendar_item.model_dump(exclude_unset=True)
            )
            new_calendars.append(calendar_info)

        for entity_description in _get_entity_descriptions(
            hass, config_entry, calendar_item, calendar_info
        ):
            unique_id = (
                f"{config_entry.unique_id}-{entity_description.key}"
                if entity_description.key
                else None
            )
            # Migrate to new unique_id format which supports
            # multiple config entries as of 2022.7
            for old_unique_id in (
                calendar_id,
                f"{calendar_id}-{entity_description.device_id}",
            ):
                if not (entity_entry := entity_entry_map.get(old_unique_id)):
                    continue
                if unique_id:
                    _LOGGER.debug(
                        "Migrating unique_id for %s from %s to %s",
                        entity_entry.entity_id,
                        old_unique_id,
                        unique_id,
                    )
                    entity_registry.async_update_entity(
                        entity_entry.entity_id, new_unique_id=unique_id
                    )
                else:
                    _LOGGER.debug(
                        "Removing entity registry entry for %s from %s",
                        entity_entry.entity_id,
                        old_unique_id,
                    )
                    entity_registry.async_remove(
                        entity_entry.entity_id,
                    )
            _LOGGER.debug("Creating entity with unique_id=%s", unique_id)
            coordinator: CalendarSyncUpdateCoordinator | CalendarQueryUpdateCoordinator
            if not entity_description.local_sync:
                coordinator = CalendarQueryUpdateCoordinator(
                    hass,
                    config_entry,
                    calendar_service,
                    entity_description.name or entity_description.key,
                    calendar_id,
                    entity_description.search,
                )
            else:
                request_template = SyncEventsRequest(
                    calendar_id=calendar_id,
                    start_time=dt_util.now() + SYNC_EVENT_MIN_TIME,
                )
                sync = CalendarEventSyncManager(
                    calendar_service,
                    store=ScopedCalendarStore(
                        store, unique_id or entity_description.device_id
                    ),
                    request_template=request_template,
                )
                coordinator = CalendarSyncUpdateCoordinator(
                    hass,
                    config_entry,
                    sync,
                    entity_description.name or entity_description.key,
                )
            entities.append(
                GoogleCalendarEntity(
                    coordinator,
                    calendar_id,
                    entity_description,
                    unique_id,
                )
            )

    async_add_entities(entities)

    if calendars and new_calendars:

        def append_calendars_to_config() -> None:
            path = hass.config.path(YAML_DEVICES)
            for calendar in new_calendars:
                update_config(path, calendar)

        await hass.async_add_executor_job(append_calendars_to_config)

    platform = entity_platform.async_get_current_platform()
    if (
        any(calendar_item.access_role.is_writer for calendar_item in result.items)
        and get_feature_access(config_entry) is FeatureAccess.read_write
    ):
        platform.async_register_entity_service(
            SERVICE_CREATE_EVENT,
            CREATE_EVENT_SCHEMA,
            async_create_event,
            required_features=CalendarEntityFeature.CREATE_EVENT,
        )