def _check_entities() -> None:
        received_zones: dict[int, NASwebZone] = {
            entry.index: entry for entry in coordinator.webio_api.zones
        }
        added = {i for i in received_zones if i not in current_zones}
        removed = {i for i in current_zones if i not in received_zones}
        entities_to_add: list[ZoneEntity] = []
        for index in added:
            webio_zone = received_zones[index]
            if not isinstance(webio_zone, NASwebZone):
                _LOGGER.error("Cannot create ZoneEntity without NASwebZone")
                continue
            new_zone = ZoneEntity(coordinator, webio_zone)
            entities_to_add.append(new_zone)
            current_zones.add(index)
        async_add_entities(entities_to_add)
        entity_registry = er.async_get(hass)
        for index in removed:
            unique_id = f"{DOMAIN}.{config.unique_id}.zone.{index}"
            if entity_id := entity_registry.async_get_entity_id(
                ALARM_CONTROL_PANEL_DOMAIN, DOMAIN, unique_id
            ):
                entity_registry.async_remove(entity_id)
                current_zones.remove(index)
            else:
                _LOGGER.warning("Failed to remove old zone: no entity_id")