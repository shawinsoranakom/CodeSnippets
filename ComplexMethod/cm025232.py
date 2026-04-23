async def async_service_handler(service: ServiceCall) -> None:
            """Map services to methods on Xiaomi Philips Lights."""
            method = SERVICE_TO_METHOD[service.service]
            params = {
                key: value
                for key, value in service.data.items()
                if key != ATTR_ENTITY_ID
            }
            if entity_ids := service.data.get(ATTR_ENTITY_ID):
                target_devices = [
                    dev
                    for dev in hass.data[DATA_KEY].values()
                    if dev.entity_id in entity_ids
                ]
            else:
                target_devices = hass.data[DATA_KEY].values()

            update_tasks = []
            for target_device in target_devices:
                if not hasattr(target_device, method.method):
                    continue
                await getattr(target_device, method.method)(**params)
                update_tasks.append(
                    asyncio.create_task(target_device.async_update_ha_state(True))
                )

            if update_tasks:
                await asyncio.wait(update_tasks)