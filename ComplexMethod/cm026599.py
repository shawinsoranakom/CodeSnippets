def _update_entities() -> None:
        """Update entities."""
        new_entities: list[OpowerSensor] = []
        current_account_device_ids: set[str] = set()
        current_account_ids: set[str] = set()

        for opower_data in coordinator.data.values():
            account = opower_data.account
            forecast = opower_data.forecast
            device_id = (
                f"{coordinator.api.utility.subdomain()}_{account.utility_account_id}"
            )
            current_account_device_ids.add(device_id)
            current_account_ids.add(account.utility_account_id)
            device = DeviceInfo(
                identifiers={(DOMAIN, device_id)},
                name=f"{account.meter_type.name} account {account.utility_account_id}",
                manufacturer="Opower",
                model=coordinator.api.utility.name(),
                entry_type=DeviceEntryType.SERVICE,
            )
            sensors: tuple[OpowerEntityDescription, ...] = COMMON_SENSORS
            if (
                account.meter_type == MeterType.ELEC
                and forecast is not None
                and forecast.unit_of_measure == UnitOfMeasure.KWH
            ):
                sensors += ELEC_SENSORS
            elif (
                account.meter_type == MeterType.GAS
                and forecast is not None
                and forecast.unit_of_measure in [UnitOfMeasure.THERM, UnitOfMeasure.CCF]
            ):
                sensors += GAS_SENSORS
            for sensor in sensors:
                sensor_key = (account.utility_account_id, sensor.key)
                if sensor_key in created_sensors:
                    continue
                created_sensors.add(sensor_key)
                new_entities.append(
                    OpowerSensor(
                        coordinator,
                        sensor,
                        account.utility_account_id,
                        device,
                        device_id,
                    )
                )

        if new_entities:
            async_add_entities(new_entities)

        # Remove any registered devices not in the current coordinator data
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)
        for device_entry in dr.async_entries_for_config_entry(
            device_registry, entry.entry_id
        ):
            device_domain_ids = {
                identifier[1]
                for identifier in device_entry.identifiers
                if identifier[0] == DOMAIN
            }
            if not device_domain_ids:
                # This device has no Opower identifiers; it may be a merged/shared
                # device owned by another integration. Do not alter it here.
                continue
            if not device_domain_ids.isdisjoint(current_account_device_ids):
                continue  # device is still active
            # Device is stale — remove its entities then detach it
            for entity_entry in er.async_entries_for_device(
                entity_registry, device_entry.id, include_disabled_entities=True
            ):
                if entity_entry.config_entry_id != entry.entry_id:
                    continue
                entity_registry.async_remove(entity_entry.entity_id)
            device_registry.async_update_device(
                device_entry.id, remove_config_entry_id=entry.entry_id
            )

        # Prune sensor tracking for accounts that are no longer present
        if created_sensors:
            stale_sensor_keys = {
                sensor_key
                for sensor_key in created_sensors
                if sensor_key[0] not in current_account_ids
            }
            if stale_sensor_keys:
                created_sensors.difference_update(stale_sensor_keys)