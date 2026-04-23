async def add_public_entities(update: bool = True) -> None:
        """Retrieve Netatmo public weather entities."""
        entities = {
            device.name: device.id
            for device in dr.async_entries_for_config_entry(
                device_registry, entry.entry_id
            )
            if device.model == "Public Weather station"
        }

        new_entities: list[NetatmoPublicSensor] = []
        for area in [
            NetatmoArea(**i) for i in entry.options.get(CONF_WEATHER_AREAS, {}).values()
        ]:
            signal_name = f"{PUBLIC}-{area.uuid}"

            if area.area_name in entities:
                entities.pop(area.area_name)

                if update:
                    async_dispatcher_send(
                        hass,
                        f"netatmo-config-{area.area_name}",
                        area,
                    )
                    continue

            await data_handler.subscribe(
                PUBLIC,
                signal_name,
                None,
                lat_ne=area.lat_ne,
                lon_ne=area.lon_ne,
                lat_sw=area.lat_sw,
                lon_sw=area.lon_sw,
                area_id=str(area.uuid),
            )

            new_entities.extend(
                NetatmoPublicSensor(data_handler, area, description)
                for description in PUBLIC_WEATHER_STATION_TYPES
            )

        for device_id in entities.values():
            device_registry.async_remove_device(device_id)

        async_add_entities(new_entities)