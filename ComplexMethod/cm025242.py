async def async_service_handler(service: ServiceCall) -> None:
        """Map services to methods on XiaomiAirPurifier."""
        method = SERVICE_TO_METHOD[service.service]
        params = {
            key: value for key, value in service.data.items() if key != ATTR_ENTITY_ID
        }
        if entity_ids := service.data.get(ATTR_ENTITY_ID):
            filtered_entities = [
                entity
                for entity in hass.data[DATA_KEY].values()
                if entity.entity_id in entity_ids
            ]
        else:
            filtered_entities = hass.data[DATA_KEY].values()

        update_tasks = []

        for entity in filtered_entities:
            entity_method = getattr(entity, method.method, None)
            if not entity_method:
                continue
            await entity_method(**params)
            update_tasks.append(asyncio.create_task(entity.async_update_ha_state(True)))

        if update_tasks:
            await asyncio.wait(update_tasks)