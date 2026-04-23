def _async_entity_listener() -> None:
        """Handle additions of select."""

        entities: list[AirzoneBaseSelect] = []

        systems_data = coordinator.data.get(AZD_SYSTEMS, {})
        received_systems = set(systems_data)
        new_systems = received_systems - added_systems
        if new_systems:
            entities.extend(
                AirzoneSystemSelect(
                    coordinator,
                    description,
                    entry,
                    system_id,
                    systems_data.get(system_id),
                )
                for system_id in new_systems
                for description in SYSTEM_SELECT_TYPES
                if description.key in systems_data.get(system_id)
            )
            added_systems.update(new_systems)

        zones_data = coordinator.data.get(AZD_ZONES, {})
        received_zones = set(zones_data)
        new_zones = received_zones - added_zones
        if new_zones:
            entities.extend(
                AirzoneZoneSelect(
                    coordinator,
                    description,
                    entry,
                    system_zone_id,
                    zones_data.get(system_zone_id),
                )
                for system_zone_id in new_zones
                for description in MAIN_ZONE_SELECT_TYPES
                if description.key in zones_data.get(system_zone_id)
                and zones_data.get(system_zone_id).get(AZD_MASTER) is True
            )
            entities.extend(
                AirzoneZoneSelect(
                    coordinator,
                    description,
                    entry,
                    system_zone_id,
                    zones_data.get(system_zone_id),
                )
                for system_zone_id in new_zones
                for description in ZONE_SELECT_TYPES
                if description.key in zones_data.get(system_zone_id)
            )
            added_zones.update(new_zones)

        async_add_entities(entities)