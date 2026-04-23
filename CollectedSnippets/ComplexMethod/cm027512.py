async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartThingsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add sensors for a config entry."""
    entry_data = entry.runtime_data
    entities = []

    entity_registry = er.async_get(hass)

    for device in entry_data.devices.values():  # pylint: disable=too-many-nested-blocks
        for capability, attributes in CAPABILITY_TO_SENSORS.items():
            for component, capabilities in device.status.items():
                if capability in capabilities:
                    for attribute, descriptions in attributes.items():
                        for description in descriptions:
                            if (
                                (
                                    not description.capability_ignore_list
                                    or not any(
                                        all(
                                            capability in device.status[MAIN]
                                            for capability in capability_list
                                        )
                                        for capability_list in description.capability_ignore_list
                                    )
                                )
                                and (
                                    not description.exists_fn
                                    or (
                                        component == MAIN
                                        and description.exists_fn(
                                            device.status[MAIN][capability][attribute]
                                        )
                                    )
                                )
                                and (
                                    component == MAIN
                                    or (
                                        description.component_fn is not None
                                        and description.component_fn(component)
                                    )
                                )
                            ):
                                if (
                                    description.deprecated
                                    and (
                                        deprecation_info := description.deprecated(
                                            device.status[MAIN]
                                        )
                                    )
                                    is not None
                                ):
                                    version, reason = deprecation_info
                                    if deprecate_entity(
                                        hass,
                                        entity_registry,
                                        SENSOR_DOMAIN,
                                        f"{device.device.device_id}_{MAIN}_{capability}_{attribute}_{description.key}",
                                        f"deprecated_{reason}",
                                        version,
                                    ):
                                        entities.append(
                                            SmartThingsSensor(
                                                entry_data.client,
                                                device,
                                                description,
                                                MAIN,
                                                capability,
                                                attribute,
                                            )
                                        )
                                    continue
                                entities.append(
                                    SmartThingsSensor(
                                        entry_data.client,
                                        device,
                                        description,
                                        component,
                                        capability,
                                        attribute,
                                    )
                                )

    async_add_entities(entities)