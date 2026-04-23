async def async_service_handler(service: ServiceCall) -> None:
            """Map services to methods on XiaomiPlugGenericSwitch."""
            method = SERVICE_TO_METHOD[service.service]
            params = {
                key: value
                for key, value in service.data.items()
                if key != ATTR_ENTITY_ID
            }
            if entity_ids := service.data.get(ATTR_ENTITY_ID):
                devices = [
                    device
                    for device in hass.data[DATA_KEY].values()
                    if device.entity_id in entity_ids
                ]
            else:
                devices = hass.data[DATA_KEY].values()

            update_tasks = []
            for device in devices:
                if not hasattr(device, method.method):
                    continue
                await getattr(device, method.method)(**params)
                update_tasks.append(
                    asyncio.create_task(device.async_update_ha_state(True))
                )

            if update_tasks:
                await asyncio.wait(update_tasks)