def _get_exposed_entities(
    hass: HomeAssistant,
    assistant: str,
    include_state: bool = True,
) -> dict[str, dict[str, dict[str, Any]]]:
    """Get exposed entities.

    Splits out calendars and scripts.
    """
    area_registry = ar.async_get(hass)
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    interesting_attributes = {
        "temperature",
        "current_temperature",
        "temperature_unit",
        "brightness",
        "humidity",
        "unit_of_measurement",
        "device_class",
        "current_position",
        "percentage",
        "volume_level",
        "media_title",
        "media_artist",
        "media_album_name",
    }

    entities = {}
    data: dict[str, dict[str, Any]] = {
        SCRIPT_DOMAIN: {},
        CALENDAR_DOMAIN: {},
    }

    for state in sorted(hass.states.async_all(), key=attrgetter("name")):
        if not async_should_expose(hass, assistant, state.entity_id):
            continue

        entity_entry = entity_registry.async_get(state.entity_id)
        device_entry = (
            device_registry.async_get(entity_entry.device_id)
            if entity_entry is not None and entity_entry.device_id is not None
            else None
        )
        names = intent.async_get_entity_aliases(hass, entity_entry, state=state)
        area_names = []

        if entity_entry is not None:
            if (
                entity_entry.area_id is not None
                and (area_entry := area_registry.async_get_area(entity_entry.area_id))
                is not None
            ):
                # Entity is in area
                area_names.append(area_entry.name)
                area_names.extend(area_entry.aliases)
            elif device_entry is not None:
                # Check device area
                if (
                    device_entry.area_id is not None
                    and (
                        area_entry := area_registry.async_get_area(device_entry.area_id)
                    )
                    is not None
                ):
                    area_names.append(area_entry.name)
                    area_names.extend(area_entry.aliases)

        info: dict[str, Any] = {
            "names": ", ".join(names),
            "domain": state.domain,
        }

        if include_state:
            info["state"] = state.state

            # Convert timestamp device_class states from UTC to local time
            if state.attributes.get("device_class") == "timestamp" and state.state:
                if (parsed_utc := dt_util.parse_datetime(state.state)) is not None:
                    info["state"] = dt_util.as_local(parsed_utc).isoformat()

        if area_names:
            info["areas"] = ", ".join(area_names)

        if include_state and (
            attributes := {
                attr_name: (
                    str(attr_value)
                    if isinstance(attr_value, (Enum, Decimal, int))
                    else attr_value
                )
                for attr_name, attr_value in state.attributes.items()
                if attr_name in interesting_attributes
            }
        ):
            info["attributes"] = attributes

        if state.domain in data:
            data[state.domain][state.entity_id] = info
        else:
            entities[state.entity_id] = info

    data["entities"] = entities
    return data