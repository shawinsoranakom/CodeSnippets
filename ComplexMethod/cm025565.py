def _handle_paired_or_connected_appliance(
    hass: HomeAssistant,
    entry: HomeConnectConfigEntry,
    known_entity_unique_ids: dict[str, str],
    get_entities_for_appliance: Callable[
        [HomeConnectApplianceCoordinator], list[HomeConnectEntity]
    ],
    get_option_entities_for_appliance: Callable[
        [HomeConnectApplianceCoordinator, er.EntityRegistry],
        list[HomeConnectEntity],
    ]
    | None,
    changed_options_listener_remove_callbacks: dict[str, list[Callable[[], None]]],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Handle a new paired appliance or an appliance that has been connected.

    This function is used to handle connected events also, because some appliances
    don't report any data while they are off because they disconnect themselves
    when they are turned off, so we need to check if the entities have been added
    already or it is the first time we see them when the appliance is connected.
    """
    entities: list[HomeConnectEntity] = []
    entity_registry = er.async_get(hass)
    for appliance_coordinator in entry.runtime_data.appliance_coordinators.values():
        appliance_ha_id = appliance_coordinator.data.info.ha_id
        entities_to_add = [
            entity
            for entity in get_entities_for_appliance(appliance_coordinator)
            if entity.unique_id not in known_entity_unique_ids
        ]
        if get_option_entities_for_appliance:
            entities_to_add.extend(
                entity
                for entity in get_option_entities_for_appliance(
                    appliance_coordinator, entity_registry
                )
                if entity.unique_id not in known_entity_unique_ids
            )
            for event_key in (
                EventKey.BSH_COMMON_ROOT_ACTIVE_PROGRAM,
                EventKey.BSH_COMMON_ROOT_SELECTED_PROGRAM,
            ):
                changed_options_listener_remove_callback = (
                    appliance_coordinator.async_add_listener(
                        partial(
                            _create_option_entities,
                            entity_registry,
                            appliance_coordinator,
                            known_entity_unique_ids,
                            get_option_entities_for_appliance,
                            async_add_entities,
                        ),
                        event_key,
                    )
                )
                entry.async_on_unload(changed_options_listener_remove_callback)
                changed_options_listener_remove_callbacks[appliance_ha_id].append(
                    changed_options_listener_remove_callback
                )
        known_entity_unique_ids.update(
            {cast(str, entity.unique_id): appliance_ha_id for entity in entities_to_add}
        )
        entities.extend(entities_to_add)
    async_add_entities(entities)