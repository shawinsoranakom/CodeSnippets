def _get_entity_descriptions(
    hass: HomeAssistant,
    config_entry: GoogleConfigEntry,
    calendar_item: Calendar,
    calendar_info: Mapping[str, Any],
) -> list[GoogleCalendarEntityDescription]:
    """Create entity descriptions for the calendar.

    The entity descriptions are based on the type of Calendar from the API
    and optional calendar_info yaml configuration that is the older way to
    configure calendars before they supported UI based config.

    The yaml config may map one calendar to multiple entities and they do not
    have a unique id. The yaml config also supports additional options like
    offsets or search.
    """
    calendar_id = calendar_item.id
    num_entities = len(calendar_info[CONF_ENTITIES])
    entity_descriptions = []
    for data in calendar_info[CONF_ENTITIES]:
        if num_entities > 1:
            key = ""
        else:
            key = calendar_id
        entity_enabled = data.get(CONF_TRACK, True)
        if not entity_enabled:
            _LOGGER.warning(
                "The 'track' option in google_calendars.yaml has been deprecated."
                " The setting has been imported to the UI, and should now be"
                " removed from google_calendars.yaml"
            )
        read_only = not (
            calendar_item.access_role.is_writer
            and get_feature_access(config_entry) is FeatureAccess.read_write
        )
        # Prefer calendar sync down of resources when possible. However,
        # sync does not work for search. Also free-busy calendars denormalize
        # recurring events as individual events which is not efficient for sync
        local_sync = True
        if (
            search := data.get(CONF_SEARCH)
        ) or calendar_item.access_role == AccessRole.FREE_BUSY_READER:
            read_only = True
            local_sync = False
        entity_description = GoogleCalendarEntityDescription(
            key=key,
            name=data[CONF_NAME].capitalize(),
            entity_id=generate_entity_id(
                ENTITY_ID_FORMAT, data[CONF_DEVICE_ID], hass=hass
            ),
            read_only=read_only,
            ignore_availability=data.get(CONF_IGNORE_AVAILABILITY, False),
            offset=data.get(CONF_OFFSET, DEFAULT_CONF_OFFSET),
            search=search,
            local_sync=local_sync,
            entity_registry_enabled_default=entity_enabled,
            device_id=data[CONF_DEVICE_ID],
            initial_color=calendar_item.background_color,
        )
        entity_descriptions.append(entity_description)
        _LOGGER.debug(
            "calendar_item.primary=%s, search=%s, calendar_item.access_role=%s - %s",
            calendar_item.primary,
            search,
            calendar_item.access_role,
            local_sync,
        )
        if calendar_item.primary and local_sync:
            # Create a separate calendar for birthdays
            entity_descriptions.append(
                dataclasses.replace(
                    entity_description,
                    key=f"{key}-birthdays",
                    translation_key="birthdays",
                    event_type=EventTypeEnum.BIRTHDAY,
                    name=None,
                    entity_id=None,
                )
            )
            # Create an optional disabled by default entity for Work Location
            entity_descriptions.append(
                dataclasses.replace(
                    entity_description,
                    key=f"{key}-work-location",
                    translation_key="working_location",
                    event_type=EventTypeEnum.WORKING_LOCATION,
                    name=None,
                    entity_id=None,
                    entity_registry_enabled_default=False,
                )
            )
    return entity_descriptions